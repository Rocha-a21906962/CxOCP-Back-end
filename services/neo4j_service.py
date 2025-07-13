import csv
import io
from neo4j import GraphDatabase

class Neo4jService:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or "bolt://localhost:7687"
        self.user = user or "neo4j"
        self.password = password or "a21906962"
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        if self.driver:
            self.driver.close()

    def ingest_csv(self, csv_content: str, process_id: str, process_name: str = None):
        with self.driver.session() as session:
            # Upsert (merge) the Process node with id and optional name
            session.run(
                "MERGE (p:Process {id: $pid}) "
                "SET p.name = $pname",
                pid=process_id, pname=process_name
            )

            reader = csv.DictReader(io.StringIO(csv_content))
            step_nodes = []
            for idx, row in enumerate(reader, start=1):
                node_id = f"{process_id}_{idx}"  # Unique per process
                step_props = dict(row)
                step_props["process_id"] = process_id
                step_props["row_num"] = idx
                step_props["step_id"] = node_id

                # Create Step node and connect to Process
                session.run(
                    """
                    MATCH (p:Process {id: $pid})
                    CREATE (s:Step $props)
                    CREATE (p)-[:HAS_STEP]->(s)
                    """,
                    pid=process_id,
                    props=step_props,
                )
                step_nodes.append(node_id)

            # Link steps in order
            for i in range(len(step_nodes) - 1):
                session.run(
                    """
                    MATCH (a:Step {step_id: $a_id}), (b:Step {step_id: $b_id})
                    MERGE (a)-[:NEXT]->(b)
                    """,
                    a_id=step_nodes[i], b_id=step_nodes[i + 1]
                )

    def delete_process(self, process_id: str):
        with self.driver.session() as session:
            # Delete the process and all steps associated with it in one query
            session.run(
                """
                MATCH (p:Process {id: $pid})
                OPTIONAL MATCH (p)-[:HAS_STEP]->(s:Step)
                DETACH DELETE p, s
                """,
                pid=process_id
            )

# Example usage:
# neo4j_service = Neo4jService()
# neo4j_service.ingest_csv(csv_content, process_id, process_name)
# neo4j_service.delete_process(process_id)
# neo4j_service.close()