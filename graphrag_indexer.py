#!/usr/bin/env python3
"""
Microsoft GraphRAG 金融業數據索引和查詢實現
演示如何定義 Entity、Node、Relationship 和 Hop
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# 模擬 GraphRAG 的核心概念
# 由於完整的 GraphRAG 需要 LLM API，我們創建一個演示版本

@dataclass
class Entity:
    """實體（Entity）- 從文本中提取的概念"""
    id: str
    name: str
    entity_type: str  # 如：客戶、產品、政策等
    description: str
    source_document: str
    
    def __repr__(self):
        return f"Entity(id={self.id}, name={self.name}, type={self.entity_type})"


@dataclass
class Node:
    """節點（Node）- 知識圖譜中的實體表示"""
    node_id: str
    entity_id: str
    name: str
    node_type: str
    description: str
    attributes: Dict[str, Any]
    community_id: Optional[int] = None
    
    def __repr__(self):
        return f"Node(id={self.node_id}, name={self.name}, type={self.node_type})"


@dataclass
class Relationship:
    """關係（Relationship）- 連接兩個節點的邊"""
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    description: str
    weight: float = 1.0
    
    def __repr__(self):
        return f"Relationship({self.source_node_id} --[{self.relationship_type}]--> {self.target_node_id})"


@dataclass
class Path:
    """路徑（Path）- 多跳推理的結果"""
    path_id: str
    nodes: List[Node]
    relationships: List[Relationship]
    hops: int
    
    def __repr__(self):
        nodes_str = " -> ".join([n.name for n in self.nodes])
        return f"Path({nodes_str}, hops={self.hops})"


class FinancialGraphRAG:
    """金融業 GraphRAG 實現"""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.nodes: Dict[str, Node] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.node_counter = 0
        self.relationship_counter = 0
        self.entity_counter = 0
        
    def create_entity(self, name: str, entity_type: str, description: str, 
                     source_document: str) -> Entity:
        """創建實體"""
        entity_id = f"E{self.entity_counter:04d}"
        self.entity_counter += 1
        
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            description=description,
            source_document=source_document
        )
        
        self.entities[entity_id] = entity
        return entity
    
    def create_node(self, entity: Entity, attributes: Dict[str, Any]) -> Node:
        """從實體創建節點"""
        node_id = f"N{self.node_counter:04d}"
        self.node_counter += 1
        
        node = Node(
            node_id=node_id,
            entity_id=entity.id,
            name=entity.name,
            node_type=entity.entity_type,
            description=entity.description,
            attributes=attributes
        )
        
        self.nodes[node_id] = node
        return node
    
    def create_relationship(self, source_node: Node, target_node: Node,
                          relationship_type: str, description: str,
                          weight: float = 1.0) -> Relationship:
        """創建關係"""
        rel_id = f"R{self.relationship_counter:04d}"
        self.relationship_counter += 1
        
        relationship = Relationship(
            relationship_id=rel_id,
            source_node_id=source_node.node_id,
            target_node_id=target_node.node_id,
            relationship_type=relationship_type,
            description=description,
            weight=weight
        )
        
        self.relationships[rel_id] = relationship
        return relationship
    
    def find_path(self, start_node_id: str, end_node_id: str, 
                 max_hops: int = 5) -> Optional[Path]:
        """使用 BFS 查找兩個節點之間的最短路徑"""
        from collections import deque
        
        queue = deque([(start_node_id, [start_node_id], [])])
        visited = {start_node_id}
        
        while queue:
            current_node_id, node_path, rel_path = queue.popleft()
            
            if len(node_path) - 1 > max_hops:
                continue
            
            if current_node_id == end_node_id:
                nodes = [self.nodes[nid] for nid in node_path]
                path = Path(
                    path_id=f"P{len(node_path)-1}HOP",
                    nodes=nodes,
                    relationships=rel_path,
                    hops=len(node_path) - 1
                )
                return path
            
            # 查找所有相連的邊
            for rel_id, rel in self.relationships.items():
                if rel.source_node_id == current_node_id and rel.target_node_id not in visited:
                    visited.add(rel.target_node_id)
                    queue.append((
                        rel.target_node_id,
                        node_path + [rel.target_node_id],
                        rel_path + [rel]
                    ))
        
        return None
    
    def get_node_neighbors(self, node_id: str, hops: int = 1) -> Dict[str, List[Node]]:
        """獲取節點的鄰居（指定跳數）"""
        neighbors = {f"{i}_hop": [] for i in range(1, hops + 1)}
        visited = set()
        current_level = {node_id}
        
        for hop in range(1, hops + 1):
            next_level = set()
            for current_id in current_level:
                for rel_id, rel in self.relationships.items():
                    if rel.source_node_id == current_id:
                        target_id = rel.target_node_id
                        if target_id not in visited and target_id != node_id:
                            neighbors[f"{hop}_hop"].append(self.nodes[target_id])
                            next_level.add(target_id)
                            visited.add(target_id)
            current_level = next_level
        
        return neighbors
    
    def search_by_entity_type(self, entity_type: str) -> List[Node]:
        """按實體類型搜索節點"""
        return [node for node in self.nodes.values() if node.node_type == entity_type]
    
    def search_by_attribute(self, attribute_name: str, attribute_value: Any) -> List[Node]:
        """按屬性搜索節點"""
        return [node for node in self.nodes.values() 
                if attribute_name in node.attributes 
                and node.attributes[attribute_name] == attribute_value]
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """獲取圖的統計信息"""
        return {
            "total_entities": len(self.entities),
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "entity_types": list(set(e.entity_type for e in self.entities.values())),
            "relationship_types": list(set(r.relationship_type for r in self.relationships.values())),
        }
    
    def export_graph(self, output_file: str):
        """導出圖為 JSON 格式"""
        graph_data = {
            "entities": [asdict(e) for e in self.entities.values()],
            "nodes": [asdict(n) for n in self.nodes.values()],
            "relationships": [asdict(r) for r in self.relationships.values()],
            "statistics": self.get_graph_statistics()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 圖已導出到 {output_file}")


def build_financial_knowledge_graph() -> FinancialGraphRAG:
    """構建金融業知識圖譜"""
    
    print("="*60)
    print("構建金融業知識圖譜")
    print("="*60)
    
    graphrag = FinancialGraphRAG()
    
    # ===== 第一步：創建實體 =====
    print("\n[步驟 1] 創建實體（Entity）")
    print("-" * 60)
    
    # 客戶實體
    entity_customer_zhangsan = graphrag.create_entity(
        name="張三",
        entity_type="客戶",
        description="科技行業專業人士，信用評分 750，年收入 50 萬元",
        source_document="customers.csv"
    )
    print(f"✓ 創建實體: {entity_customer_zhangsan}")
    
    entity_customer_lisi = graphrag.create_entity(
        name="李四",
        entity_type="客戶",
        description="製造業工作者，信用評分 680，年收入 35 萬元",
        source_document="customers.csv"
    )
    print(f"✓ 創建實體: {entity_customer_lisi}")
    
    # 貸款產品實體
    entity_product_credit = graphrag.create_entity(
        name="個人信用貸款",
        entity_type="貸款產品",
        description="無擔保貸款，利率 4.5%，期限 12-60 個月",
        source_document="loan_products.csv"
    )
    print(f"✓ 創建實體: {entity_product_credit}")
    
    entity_product_business = graphrag.create_entity(
        name="企業經營貸",
        entity_type="貸款產品",
        description="商業貸款，利率 5.2%，期限 12-84 個月",
        source_document="loan_products.csv"
    )
    print(f"✓ 創建實體: {entity_product_business}")
    
    # 政策實體
    entity_policy_credit = graphrag.create_entity(
        name="信用貸款政策",
        entity_type="政策",
        description="個人信用貸款的審批標準和風險控制，最低信用評分 600",
        source_document="policies.csv"
    )
    print(f"✓ 創建實體: {entity_policy_credit}")
    
    entity_policy_business = graphrag.create_entity(
        name="企業貸款政策",
        entity_type="政策",
        description="企業貸款的審批標準，最低信用評分 650",
        source_document="policies.csv"
    )
    print(f"✓ 創建實體: {entity_policy_business}")
    
    # 銀行實體
    entity_bank = graphrag.create_entity(
        name="商業銀行",
        entity_type="銀行",
        description="提供各類貸款產品的商業銀行",
        source_document="financial_documents.txt"
    )
    print(f"✓ 創建實體: {entity_bank}")
    
    # ===== 第二步：創建節點 =====
    print("\n[步驟 2] 創建節點（Node）- 將實體放入知識圖譜")
    print("-" * 60)
    
    # 客戶節點
    node_customer_zhangsan = graphrag.create_node(
        entity_customer_zhangsan,
        attributes={
            "customer_id": "C001",
            "credit_score": 750,
            "annual_income": 500000,
            "industry": "科技",
            "risk_level": "低風險"
        }
    )
    print(f"✓ 創建節點: {node_customer_zhangsan}")
    
    node_customer_lisi = graphrag.create_node(
        entity_customer_lisi,
        attributes={
            "customer_id": "C002",
            "credit_score": 680,
            "annual_income": 350000,
            "industry": "製造",
            "risk_level": "中風險"
        }
    )
    print(f"✓ 創建節點: {node_customer_lisi}")
    
    # 產品節點
    node_product_credit = graphrag.create_node(
        entity_product_credit,
        attributes={
            "product_id": "P001",
            "interest_rate": 4.5,
            "loan_term": "12-60",
            "min_amount": 50000,
            "max_amount": 500000,
            "min_credit_score": 600,
            "risk_category": "低風險"
        }
    )
    print(f"✓ 創建節點: {node_product_credit}")
    
    node_product_business = graphrag.create_node(
        entity_product_business,
        attributes={
            "product_id": "P003",
            "interest_rate": 5.2,
            "loan_term": "12-84",
            "min_amount": 100000,
            "max_amount": 10000000,
            "min_credit_score": 650,
            "risk_category": "中風險"
        }
    )
    print(f"✓ 創建節點: {node_product_business}")
    
    # 政策節點
    node_policy_credit = graphrag.create_node(
        entity_policy_credit,
        attributes={
            "policy_id": "POL001",
            "min_credit_score": 600,
            "max_debt_ratio": 0.5,
            "collateral_required": False
        }
    )
    print(f"✓ 創建節點: {node_policy_credit}")
    
    node_policy_business = graphrag.create_node(
        entity_policy_business,
        attributes={
            "policy_id": "POL003",
            "min_credit_score": 650,
            "max_debt_ratio": 0.6,
            "collateral_required": True
        }
    )
    print(f"✓ 創建節點: {node_policy_business}")
    
    # 銀行節點
    node_bank = graphrag.create_node(
        entity_bank,
        attributes={
            "bank_name": "商業銀行",
            "total_customers": 8,
            "total_products": 6
        }
    )
    print(f"✓ 創建節點: {node_bank}")
    
    # ===== 第三步：創建關係 =====
    print("\n[步驟 3] 創建關係（Relationship）- 連接節點")
    print("-" * 60)
    
    # 客戶申請產品
    rel_zhangsan_applies_credit = graphrag.create_relationship(
        source_node=node_customer_zhangsan,
        target_node=node_product_credit,
        relationship_type="申請",
        description="張三於 2024-01-15 申請個人信用貸款，金額 20 萬元，已批准",
        weight=1.0
    )
    print(f"✓ 創建關係: {rel_zhangsan_applies_credit}")
    
    rel_lisi_applies_business = graphrag.create_relationship(
        source_node=node_customer_lisi,
        target_node=node_product_business,
        relationship_type="申請",
        description="李四於 2024-01-20 申請企業經營貸，金額 50 萬元，待審核",
        weight=1.0
    )
    print(f"✓ 創建關係: {rel_lisi_applies_business}")
    
    # 銀行提供產品
    rel_bank_provides_credit = graphrag.create_relationship(
        source_node=node_bank,
        target_node=node_product_credit,
        relationship_type="提供",
        description="商業銀行提供個人信用貸款產品",
        weight=1.0
    )
    print(f"✓ 創建關係: {rel_bank_provides_credit}")
    
    rel_bank_provides_business = graphrag.create_relationship(
        source_node=node_bank,
        target_node=node_product_business,
        relationship_type="提供",
        description="商業銀行提供企業經營貸產品",
        weight=1.0
    )
    print(f"✓ 創建關係: {rel_bank_provides_business}")
    
    # 產品受限於政策
    rel_credit_limited_by_policy = graphrag.create_relationship(
        source_node=node_product_credit,
        target_node=node_policy_credit,
        relationship_type="受限於",
        description="個人信用貸款受信用貸款政策的限制",
        weight=1.0
    )
    print(f"✓ 創建關係: {rel_credit_limited_by_policy}")
    
    rel_business_limited_by_policy = graphrag.create_relationship(
        source_node=node_product_business,
        target_node=node_policy_business,
        relationship_type="受限於",
        description="企業經營貸受企業貸款政策的限制",
        weight=1.0
    )
    print(f"✓ 創建關係: {rel_business_limited_by_policy}")
    
    # ===== 第四步：多跳推理 =====
    print("\n[步驟 4] 多跳推理（Hop）- 查找路徑")
    print("-" * 60)
    
    # 1-Hop: 直接連接
    print("\n1-Hop 推理（直接連接）:")
    neighbors_1hop = graphrag.get_node_neighbors(node_customer_zhangsan.node_id, hops=1)
    print(f"  張三的 1-Hop 鄰居: {[n.name for n in neighbors_1hop['1_hop']]}")
    
    # 2-Hop: 間接連接
    print("\n2-Hop 推理（間接連接）:")
    neighbors_2hop = graphrag.get_node_neighbors(node_customer_zhangsan.node_id, hops=2)
    print(f"  張三的 2-Hop 鄰居: {[n.name for n in neighbors_2hop['2_hop']]}")
    
    # 查找路徑
    print("\n路徑查詢:")
    path = graphrag.find_path(node_customer_zhangsan.node_id, node_policy_credit.node_id)
    if path:
        print(f"  ✓ 找到路徑: {path}")
        print(f"    路徑長度: {path.hops} Hop")
        print(f"    路徑: {' -> '.join([n.name for n in path.nodes])}")
    
    # ===== 第五步：搜索和查詢 =====
    print("\n[步驟 5] 搜索和查詢")
    print("-" * 60)
    
    # 按實體類型搜索
    customers = graphrag.search_by_entity_type("客戶")
    print(f"\n所有客戶節點: {[n.name for n in customers]}")
    
    products = graphrag.search_by_entity_type("貸款產品")
    print(f"所有貸款產品節點: {[n.name for n in products]}")
    
    # 按屬性搜索
    high_credit_customers = graphrag.search_by_attribute("credit_score", 750)
    print(f"\n信用評分為 750 的客戶: {[n.name for n in high_credit_customers]}")
    
    # ===== 統計信息 =====
    print("\n[步驟 6] 圖統計信息")
    print("-" * 60)
    stats = graphrag.get_graph_statistics()
    print(f"總實體數: {stats['total_entities']}")
    print(f"總節點數: {stats['total_nodes']}")
    print(f"總關係數: {stats['total_relationships']}")
    print(f"實體類型: {stats['entity_types']}")
    print(f"關係類型: {stats['relationship_types']}")
    
    # 導出圖
    graphrag.export_graph("financial_graph.json")
    
    return graphrag


if __name__ == "__main__":
    graphrag = build_financial_knowledge_graph()
    print("\n" + "="*60)
    print("✓ 知識圖譜構建完成！")
    print("="*60)
