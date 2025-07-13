import os
import re
from datetime import datetime
from neo4j import GraphDatabase
from openai import OpenAI
from core.config import Settings

class Neo4jRAGService:
    def __init__(self):
        settings = Settings()
        self.neo4j_uri = os.getenv('NEO4J_URI', getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687'))
        self.neo4j_user = os.getenv('NEO4J_USER', getattr(settings, 'NEO4J_USER', 'neo4j'))
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', getattr(settings, 'NEO4J_PASSWORD', 'a21906962'))
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.schema_cache = None
        self.schema_last_updated = None
        self.cache_duration_minutes = 60

    def get_database_schema(self, force_refresh=False):
        cache_expired = (self.schema_last_updated and 
                         (datetime.now() - self.schema_last_updated).seconds > (self.cache_duration_minutes * 60))
        if (self.schema_cache is None or force_refresh or cache_expired):
            driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            try:
                with driver.session() as session:
                    node_labels_result = session.run("CALL db.labels()").data()
                    node_labels = [label['label'] for label in node_labels_result]

                    rel_types = session.run("CALL db.relationshipTypes()").data()
                    relationship_patterns = []
                    for rel_type in rel_types:
                        rel_name = rel_type['relationshipType']
                        pattern_query = f"""
                        MATCH (a)-[r:{rel_name}]->(b) 
                        RETURN DISTINCT 
                            labels(a)[0] as source_type,
                            type(r) as relationship,
                            labels(b)[0] as target_type,
                            count(*) as instances
                        ORDER BY instances DESC
                        """
                        results = session.run(pattern_query).data()
                        for result in results:
                            pattern = {
                                'pattern': f"({result['source_type']})-[:{result['relationship']}]->({result['target_type']})",
                                'source': result['source_type'],
                                'relationship': result['relationship'],
                                'target': result['target_type'],
                                'count': result['instances'],
                            }
                            relationship_patterns.append(pattern)

                    schema_info = {}
                    for label in node_labels:
                        sample_query = f"MATCH (n:{label}) RETURN keys(n) as properties LIMIT 1"
                        props_result = session.run(sample_query).data()
                        schema_info[label] = props_result[0]['properties'] if props_result else []

                self.schema_cache = {
                    'nodes': node_labels,
                    'relationship_patterns': relationship_patterns,
                    'properties': schema_info,
                    'discovery_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.schema_last_updated = datetime.now()
            except Exception as e:
                print(f"Error discovering schema: {e}")
                return None
            finally:
                driver.close()
        return self.schema_cache

    def generate_dynamic_cypher(self, question, schema):
        schema_description = f"""
Available Node Types: {', '.join(schema['nodes'])}

EXACT RELATIONSHIP PATTERNS:
"""
        for pattern in schema['relationship_patterns']:
            schema_description += f"- {pattern['pattern']} ({pattern['count']} instances)\n"
        schema_description += f"\nNode Properties:\n"
        for node, props in schema['properties'].items():
            schema_description += f"- {node}: {', '.join(props) if props else 'no properties found'}\n"

        prompt = f"""
You are a Cypher query generator. Generate ONLY a syntactically correct Cypher query.

Database Schema:
{schema_description}

User Question: "{question}"

RULES:
- Return ONLY the Cypher query, no explanations, markdown, or text
- WHERE clauses must come AFTER all MATCH clauses
- Use proper Cypher syntax

Current Question: "{question}"
Cypher query:
"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.05
        )
        query = response.choices[0].message.content.strip()
        query = self.clean_query_response(query)
        return query

    def clean_query_response(self, query):
        prefixes_to_remove = [
            "Here is the syntactically correct Cypher query:",
            "The corrected query is:",
            "CORRECTED QUERY:",
            "Query:",
            "Cypher query:",
            "The query is:",
            "Answer:"
        ]
        for prefix in prefixes_to_remove:
            if query.lower().startswith(prefix.lower()):
                query = query[len(prefix):].strip()
        if query.startswith("```cypher"):
            query = query[10:].strip()
        elif query.startswith("```"):
            query = query[3:].strip()
        if query.endswith("```"):
            query = query[:-3].strip()
        lines = query.split('\n')
        cypher_started = False
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if any(line.upper().startswith(keyword) for keyword in ['MATCH', 'RETURN', 'WHERE', 'WITH', 'UNION', 'ORDER']):
                cypher_started = True
            if cypher_started:
                cleaned_lines.append(line)
        result = '\n'.join(cleaned_lines).strip()
        return result if result else query

    def execute_cypher(self, cypher_query):
        driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        try:
            with driver.session() as session:
                result = session.run(cypher_query)
                facts = []
                for row in result:
                    row_dict = dict(row)
                    fact_parts = []
                    for key, value in row_dict.items():
                        if value is None:
                            continue
                        elif isinstance(value, list):
                            if value:
                                fact_parts.append(f"{key}: {', '.join(map(str, value))}")
                        elif hasattr(value, 'keys'):  # Neo4j node/relationship object
                            props = dict(value)
                            if props:
                                prop_strs = [f"{k}={v}" for k, v in props.items()]
                                fact_parts.append(f"{key}: {{{', '.join(prop_strs)}}}")
                        else:
                            fact_parts.append(f"{key}: {value}")
                    if fact_parts:
                        facts.append("; ".join(fact_parts))
                if facts:
                    context = ". ".join(facts) + "."
                    return context
                else:
                    return "No data found matching your query."
        except Exception as e:
            return f"I encountered an error while querying the database: {e}"
        finally:
            driver.close()

    def generate_contextual_answer(self, context, question):
        if context.startswith("I encountered an error") or context.startswith("No data found"):
            return context
        prompt = f"""
Context from database: {context}
User question: {question}

Please provide a clear, helpful answer based on the context:
- Be conversational and natural
- Structure the information clearly with bullet points or numbers when appropriate
- If there's a lot of data, summarize key points
- If the context seems incomplete, acknowledge that
- Use proper formatting for better readability

Answer:
"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    def process_question(self, question):
        schema = self.get_database_schema()
        if not schema:
            return "I couldn't connect to the database or discover its structure."
        cypher_query = self.generate_dynamic_cypher(question, schema)
        context = self.execute_cypher(cypher_query)
        answer = self.generate_contextual_answer(context, question)
        return answer