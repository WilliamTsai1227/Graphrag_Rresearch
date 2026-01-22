#!/usr/bin/env python3
"""
Python FastAPI 後端應用
整合 GraphRAG 知識圖譜查詢功能
提供生成式搜索和多跳推理接口
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from graphrag_indexer import (
    FinancialGraphRAG, 
    Entity, 
    Node, 
    Relationship, 
    Path,
    build_financial_knowledge_graph
)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 應用
app = FastAPI(
    title="金融業 GraphRAG 查詢系統",
    description="使用 Microsoft GraphRAG 進行知識圖譜查詢和多跳推理",
    version="1.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 數據模型 =====

class EntityResponse(BaseModel):
    """實體響應模型"""
    id: str
    name: str
    entity_type: str
    description: str
    source_document: str

class NodeResponse(BaseModel):
    """節點響應模型"""
    node_id: str
    entity_id: str
    name: str
    node_type: str
    description: str
    attributes: Dict[str, Any]
    community_id: Optional[int] = None

class RelationshipResponse(BaseModel):
    """關係響應模型"""
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    description: str
    weight: float

class PathResponse(BaseModel):
    """路徑響應模型"""
    path_id: str
    nodes: List[NodeResponse]
    relationships: List[RelationshipResponse]
    hops: int

class SearchQuery(BaseModel):
    """搜索查詢模型"""
    query_type: str  # "entity", "node", "path", "neighbors"
    query_text: str
    max_results: int = 10
    max_hops: int = 3

class SearchResponse(BaseModel):
    """搜索響應模型"""
    query: str
    query_type: str
    results: List[Dict[str, Any]]
    total_results: int
    execution_time: float
    timestamp: str

class GraphStatistics(BaseModel):
    """圖統計模型"""
    total_entities: int
    total_nodes: int
    total_relationships: int
    entity_types: List[str]
    relationship_types: List[str]

# ===== 全局變量 =====

graphrag: Optional[FinancialGraphRAG] = None

# ===== 初始化 =====

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化 GraphRAG"""
    global graphrag
    logger.info("初始化 GraphRAG...")
    graphrag = build_financial_knowledge_graph()
    logger.info("GraphRAG 初始化完成")

# ===== API 端點 =====

@app.get("/", tags=["基本"])
async def root():
    """根端點"""
    return {
        "message": "金融業 GraphRAG 查詢系統",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search",
            "entities": "/api/entities",
            "nodes": "/api/nodes",
            "relationships": "/api/relationships",
            "paths": "/api/paths",
            "neighbors": "/api/neighbors",
            "statistics": "/api/statistics"
        }
    }

@app.get("/health", tags=["基本"])
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "graphrag_initialized": graphrag is not None
    }

@app.post("/api/search", response_model=SearchResponse, tags=["搜索"])
async def search(query: SearchQuery):
    """
    通用搜索端點
    支持多種搜索類型：entity, node, path, neighbors
    """
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    import time
    start_time = time.time()
    
    try:
        results = []
        
        if query.query_type == "entity":
            # 按實體名稱搜索
            for entity in graphrag.entities.values():
                if query.query_text.lower() in entity.name.lower():
                    results.append({
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.entity_type,
                        "description": entity.description
                    })
        
        elif query.query_type == "node":
            # 按節點名稱搜索
            for node in graphrag.nodes.values():
                if query.query_text.lower() in node.name.lower():
                    results.append({
                        "node_id": node.node_id,
                        "name": node.name,
                        "type": node.node_type,
                        "description": node.description,
                        "attributes": node.attributes
                    })
        
        elif query.query_type == "node_type":
            # 按節點類型搜索
            nodes = graphrag.search_by_entity_type(query.query_text)
            for node in nodes[:query.max_results]:
                results.append({
                    "node_id": node.node_id,
                    "name": node.name,
                    "type": node.node_type,
                    "description": node.description,
                    "attributes": node.attributes
                })
        
        elif query.query_type == "attribute":
            # 按屬性搜索 (格式: "attribute_name:value")
            if ":" in query.query_text:
                attr_name, attr_value = query.query_text.split(":", 1)
                # 嘗試轉換為數字
                try:
                    attr_value = int(attr_value)
                except ValueError:
                    try:
                        attr_value = float(attr_value)
                    except ValueError:
                        pass
                
                nodes = graphrag.search_by_attribute(attr_name.strip(), attr_value)
                for node in nodes[:query.max_results]:
                    results.append({
                        "node_id": node.node_id,
                        "name": node.name,
                        "type": node.node_type,
                        "attributes": node.attributes
                    })
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=query.query_text,
            query_type=query.query_type,
            results=results[:query.max_results],
            total_results=len(results),
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"搜索錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/entities", response_model=List[EntityResponse], tags=["實體"])
async def get_entities(
    entity_type: Optional[str] = Query(None, description="按類型過濾"),
    limit: int = Query(100, ge=1, le=1000)
):
    """獲取所有實體"""
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    entities = list(graphrag.entities.values())
    
    if entity_type:
        entities = [e for e in entities if e.entity_type == entity_type]
    
    return [
        EntityResponse(
            id=e.id,
            name=e.name,
            entity_type=e.entity_type,
            description=e.description,
            source_document=e.source_document
        )
        for e in entities[:limit]
    ]

@app.get("/api/nodes", response_model=List[NodeResponse], tags=["節點"])
async def get_nodes(
    node_type: Optional[str] = Query(None, description="按類型過濾"),
    limit: int = Query(100, ge=1, le=1000)
):
    """獲取所有節點"""
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    nodes = list(graphrag.nodes.values())
    
    if node_type:
        nodes = [n for n in nodes if n.node_type == node_type]
    
    return [
        NodeResponse(
            node_id=n.node_id,
            entity_id=n.entity_id,
            name=n.name,
            node_type=n.node_type,
            description=n.description,
            attributes=n.attributes,
            community_id=n.community_id
        )
        for n in nodes[:limit]
    ]

@app.get("/api/relationships", response_model=List[RelationshipResponse], tags=["關係"])
async def get_relationships(
    rel_type: Optional[str] = Query(None, description="按類型過濾"),
    limit: int = Query(100, ge=1, le=1000)
):
    """獲取所有關係"""
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    relationships = list(graphrag.relationships.values())
    
    if rel_type:
        relationships = [r for r in relationships if r.relationship_type == rel_type]
    
    return [
        RelationshipResponse(
            relationship_id=r.relationship_id,
            source_node_id=r.source_node_id,
            target_node_id=r.target_node_id,
            relationship_type=r.relationship_type,
            description=r.description,
            weight=r.weight
        )
        for r in relationships[:limit]
    ]

@app.get("/api/paths/{start_node_id}/{end_node_id}", response_model=Optional[PathResponse], tags=["路徑"])
async def find_path(
    start_node_id: str,
    end_node_id: str,
    max_hops: int = Query(5, ge=1, le=10)
):
    """
    查找兩個節點之間的路徑（多跳推理）
    
    示例: /api/paths/N0000/N0004
    這將查找從節點 N0000 到節點 N0004 的路徑
    """
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    try:
        path = graphrag.find_path(start_node_id, end_node_id, max_hops)
        
        if not path:
            return None
        
        return PathResponse(
            path_id=path.path_id,
            nodes=[
                NodeResponse(
                    node_id=n.node_id,
                    entity_id=n.entity_id,
                    name=n.name,
                    node_type=n.node_type,
                    description=n.description,
                    attributes=n.attributes,
                    community_id=n.community_id
                )
                for n in path.nodes
            ],
            relationships=[
                RelationshipResponse(
                    relationship_id=r.relationship_id,
                    source_node_id=r.source_node_id,
                    target_node_id=r.target_node_id,
                    relationship_type=r.relationship_type,
                    description=r.description,
                    weight=r.weight
                )
                for r in path.relationships
            ],
            hops=path.hops
        )
    
    except Exception as e:
        logger.error(f"路徑查詢錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/neighbors/{node_id}", tags=["鄰居"])
async def get_neighbors(
    node_id: str,
    hops: int = Query(1, ge=1, le=5)
):
    """
    獲取節點的鄰居（指定跳數）
    
    示例: /api/neighbors/N0000?hops=2
    這將獲取節點 N0000 的 2-Hop 鄰居
    """
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    if node_id not in graphrag.nodes:
        raise HTTPException(status_code=404, detail=f"節點 {node_id} 不存在")
    
    try:
        neighbors = graphrag.get_node_neighbors(node_id, hops)
        
        result = {
            "node_id": node_id,
            "node_name": graphrag.nodes[node_id].name,
            "neighbors": {}
        }
        
        for hop_key, neighbor_list in neighbors.items():
            result["neighbors"][hop_key] = [
                {
                    "node_id": n.node_id,
                    "name": n.name,
                    "type": n.node_type,
                    "attributes": n.attributes
                }
                for n in neighbor_list
            ]
        
        return result
    
    except Exception as e:
        logger.error(f"鄰居查詢錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/statistics", response_model=GraphStatistics, tags=["統計"])
async def get_statistics():
    """獲取圖的統計信息"""
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    stats = graphrag.get_graph_statistics()
    
    return GraphStatistics(
        total_entities=stats["total_entities"],
        total_nodes=stats["total_nodes"],
        total_relationships=stats["total_relationships"],
        entity_types=stats["entity_types"],
        relationship_types=stats["relationship_types"]
    )

@app.get("/api/node/{node_id}", response_model=NodeResponse, tags=["節點"])
async def get_node_details(node_id: str):
    """獲取節點詳細信息"""
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    if node_id not in graphrag.nodes:
        raise HTTPException(status_code=404, detail=f"節點 {node_id} 不存在")
    
    node = graphrag.nodes[node_id]
    
    return NodeResponse(
        node_id=node.node_id,
        entity_id=node.entity_id,
        name=node.name,
        node_type=node.node_type,
        description=node.description,
        attributes=node.attributes,
        community_id=node.community_id
    )

@app.post("/api/query", tags=["查詢"])
async def execute_query(query: Dict[str, Any]):
    """
    執行自定義查詢
    
    支持的查詢類型：
    - find_path: 查找路徑
    - get_neighbors: 獲取鄰居
    - search_by_type: 按類型搜索
    - search_by_attribute: 按屬性搜索
    """
    if not graphrag:
        raise HTTPException(status_code=503, detail="GraphRAG 未初始化")
    
    query_type = query.get("type")
    
    try:
        if query_type == "find_path":
            start = query.get("start_node_id")
            end = query.get("end_node_id")
            max_hops = query.get("max_hops", 5)
            
            path = graphrag.find_path(start, end, max_hops)
            
            if path:
                return {
                    "success": True,
                    "result": {
                        "path_id": path.path_id,
                        "hops": path.hops,
                        "nodes": [n.name for n in path.nodes],
                        "relationships": [r.relationship_type for r in path.relationships]
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "未找到路徑"
                }
        
        elif query_type == "get_neighbors":
            node_id = query.get("node_id")
            hops = query.get("hops", 1)
            
            neighbors = graphrag.get_node_neighbors(node_id, hops)
            
            return {
                "success": True,
                "result": {
                    "node_id": node_id,
                    "neighbors": {
                        k: [n.name for n in v]
                        for k, v in neighbors.items()
                    }
                }
            }
        
        elif query_type == "search_by_type":
            entity_type = query.get("entity_type")
            nodes = graphrag.search_by_entity_type(entity_type)
            
            return {
                "success": True,
                "result": {
                    "entity_type": entity_type,
                    "nodes": [
                        {
                            "node_id": n.node_id,
                            "name": n.name,
                            "attributes": n.attributes
                        }
                        for n in nodes
                    ]
                }
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"未知的查詢類型: {query_type}")
    
    except Exception as e:
        logger.error(f"查詢執行錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ===== 錯誤處理 =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 異常處理"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("="*60)
    print("啟動金融業 GraphRAG 查詢系統")
    print("="*60)
    print("\n訪問 API 文檔: http://localhost:8000/docs")
    print("訪問 ReDoc: http://localhost:8000/redoc")
    print("\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
