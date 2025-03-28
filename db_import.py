from neo4j import GraphDatabase
import json
import os
    
# Neo4j 连接信息
uri = "bolt://solarsuna.com:37687"  # 更改为你的 Neo4j 地址
username = "neo4j"
password = "jack1234"  # 更改为你的密码

# JSON 文件目录
json_dir = "./docs_jmanga/"  # 更改为你的 JSON 文件目录

# 创建 Neo4j 驱动程序实例
driver = GraphDatabase.driver(uri, auth=(username, password))

# 定义 Cypher 查询
def create_manga_entity(tx, manga):
    cypher = """
    MERGE (m:Manga {url: $url})  // 使用 URL 作为唯一标识符
    WITH m, 
         CASE 
             WHEN m.name IS NULL OR m.name = '' 
             THEN true 
             ELSE false 
         END as shouldUpdate
    
    // 只在新建節點或 name 為空時更新所有屬性
    SET m += CASE shouldUpdate
        WHEN true THEN {
            name: $short_title,
            title: $title,
            chapters: toInteger($chapter_count),
            image: $image
        }
        ELSE {}
        END

    // 只在新建節點或 name 為空時更新關係
    FOREACH (genre IN CASE shouldUpdate WHEN true THEN $genres ELSE [] END |
        MERGE (g:Genre {name: genre})
        MERGE (m)-[:HAS_GENRE]->(g)
    )

    FOREACH (relatedManga IN CASE shouldUpdate WHEN true THEN $related_manga ELSE [] END |
        MERGE (rm:Manga {url: relatedManga.url})
        ON CREATE SET rm.title = relatedManga.title
        MERGE (m)-[:RELATED_TO]->(rm)
    )
    """
    tx.run(cypher,
        title=manga["title"],
        short_title=manga["short_title"],
        chapter_count=manga["chapter_count"],
        url=manga["url"],
        status=manga["status"],
        summary=manga["summary"],
        image=manga["image"],
        genres=manga["genres"],
        related_manga=manga["related_manga"]
    )


files = [ fname for fname in os.listdir(json_dir) if fname.endswith(".json") ]

# 遍历 JSON 文件并导入数据
with driver.session() as session:
    for filename in files:
        file_path = os.path.join(json_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            manga_data = json.load(f)
            session.execute_write(create_manga_entity, manga_data)
            print(f"Imported: {filename}")

# 关闭驱动程序
driver.close()
