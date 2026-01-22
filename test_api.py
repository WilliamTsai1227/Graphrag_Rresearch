#!/usr/bin/env python3
"""
GraphRAG API 測試腳本
演示各種查詢和推理功能
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class APITester:
    """API 測試器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def print_section(self, title: str):
        """打印分隔符"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60 + "\n")
    
    def print_result(self, title: str, result: Dict[str, Any]):
        """打印結果"""
        print(f"\n{title}:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    def test_health(self):
        """測試健康檢查"""
        self.print_section("1. 健康檢查")
        
        response = self.session.get(f"{self.base_url}/health")
        result = response.json()
        self.print_result("健康檢查結果", result)
        
        return response.status_code == 200
    
    def test_statistics(self):
        """測試統計信息"""
        self.print_section("2. 圖統計信息")
        
        response = self.session.get(f"{self.base_url}/api/statistics")
        result = response.json()
        self.print_result("圖統計", result)
        
        return response.status_code == 200
    
    def test_search_entity(self):
        """測試實體搜索"""
        self.print_section("3. 搜索實體 - 查找 '張三'")
        
        query = {
            "query_type": "entity",
            "query_text": "張三",
            "max_results": 10
        }
        
        response = self.session.post(f"{self.base_url}/api/search", json=query)
        result = response.json()
        self.print_result("搜索結果", result)
        
        return response.status_code == 200
    
    def test_search_by_type(self):
        """測試按類型搜索"""
        self.print_section("4. 按類型搜索 - 查找所有 '客戶'")
        
        query = {
            "query_type": "node_type",
            "query_text": "客戶",
            "max_results": 10
        }
        
        response = self.session.post(f"{self.base_url}/api/search", json=query)
        result = response.json()
        self.print_result("搜索結果", result)
        
        return response.status_code == 200
    
    def test_search_by_attribute(self):
        """測試按屬性搜索"""
        self.print_section("5. 按屬性搜索 - 信用評分 750")
        
        query = {
            "query_type": "attribute",
            "query_text": "credit_score:750",
            "max_results": 10
        }
        
        response = self.session.post(f"{self.base_url}/api/search", json=query)
        result = response.json()
        self.print_result("搜索結果", result)
        
        return response.status_code == 200
    
    def test_get_entities(self):
        """測試獲取所有實體"""
        self.print_section("6. 獲取所有實體")
        
        response = self.session.get(f"{self.base_url}/api/entities?limit=10")
        result = response.json()
        
        print(f"找到 {len(result)} 個實體:")
        for entity in result[:3]:
            print(f"  - {entity['name']} ({entity['entity_type']})")
        
        return response.status_code == 200
    
    def test_get_nodes(self):
        """測試獲取所有節點"""
        self.print_section("7. 獲取所有節點")
        
        response = self.session.get(f"{self.base_url}/api/nodes?limit=10")
        result = response.json()
        
        print(f"找到 {len(result)} 個節點:")
        for node in result[:3]:
            print(f"  - {node['name']} ({node['node_type']}, ID: {node['node_id']})")
        
        return response.status_code == 200
    
    def test_get_relationships(self):
        """測試獲取所有關係"""
        self.print_section("8. 獲取所有關係")
        
        response = self.session.get(f"{self.base_url}/api/relationships?limit=10")
        result = response.json()
        
        print(f"找到 {len(result)} 個關係:")
        for rel in result[:3]:
            print(f"  - {rel['source_node_id']} --[{rel['relationship_type']}]--> {rel['target_node_id']}")
        
        return response.status_code == 200
    
    def test_find_path(self):
        """測試路徑查詢（多跳推理）"""
        self.print_section("9. 多跳推理 - 查找從 N0000 到 N0004 的路徑")
        print("這將展示客戶 -> 貸款產品 -> 政策 的 2-Hop 推理\n")
        
        response = self.session.get(f"{self.base_url}/api/paths/N0000/N0004?max_hops=5")
        
        if response.status_code == 200:
            result = response.json()
            if result:
                print(f"找到路徑 ({result['hops']} Hop):")
                
                # 打印路徑
                path_str = " -> ".join([f"{n['name']}({n['node_type']})" for n in result['nodes']])
                print(f"  {path_str}")
                
                # 打印關係
                print("\n關係詳情:")
                for rel in result['relationships']:
                    print(f"  - {rel['relationship_type']}: {rel['description']}")
                
                self.print_result("完整結果", result)
            else:
                print("未找到路徑")
        else:
            print(f"錯誤: {response.status_code}")
        
        return response.status_code == 200
    
    def test_get_neighbors(self):
        """測試獲取鄰居"""
        self.print_section("10. 獲取節點鄰居 - N0000 的 2-Hop 鄰居")
        
        response = self.session.get(f"{self.base_url}/api/neighbors/N0000?hops=2")
        result = response.json()
        
        print(f"節點: {result['node_name']} (ID: {result['node_id']})\n")
        
        for hop_key, neighbors in result['neighbors'].items():
            print(f"{hop_key}:")
            for neighbor in neighbors:
                print(f"  - {neighbor['name']} ({neighbor['type']})")
        
        return response.status_code == 200
    
    def test_node_details(self):
        """測試獲取節點詳細信息"""
        self.print_section("11. 獲取節點詳細信息 - N0000")
        
        response = self.session.get(f"{self.base_url}/api/node/N0000")
        result = response.json()
        self.print_result("節點詳情", result)
        
        return response.status_code == 200
    
    def test_custom_query(self):
        """測試自定義查詢"""
        self.print_section("12. 自定義查詢 - 查找所有客戶")
        
        query = {
            "type": "search_by_type",
            "entity_type": "客戶"
        }
        
        response = self.session.post(f"{self.base_url}/api/query", json=query)
        result = response.json()
        self.print_result("查詢結果", result)
        
        return response.status_code == 200
    
    def run_all_tests(self):
        """運行所有測試"""
        print("\n")
        print("█" * 60)
        print("█  Microsoft GraphRAG API 測試套件")
        print("█" * 60)
        
        tests = [
            ("健康檢查", self.test_health),
            ("統計信息", self.test_statistics),
            ("實體搜索", self.test_search_entity),
            ("按類型搜索", self.test_search_by_type),
            ("按屬性搜索", self.test_search_by_attribute),
            ("獲取實體", self.test_get_entities),
            ("獲取節點", self.test_get_nodes),
            ("獲取關係", self.test_get_relationships),
            ("多跳推理", self.test_find_path),
            ("獲取鄰居", self.test_get_neighbors),
            ("節點詳情", self.test_node_details),
            ("自定義查詢", self.test_custom_query),
        ]
        
        results = {}
        start_time = time.time()
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"\n❌ 測試失敗: {str(e)}")
                results[test_name] = False
        
        elapsed_time = time.time() - start_time
        
        # 打印摘要
        self.print_section("測試摘要")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"通過: {passed}/{total}")
        print(f"總耗時: {elapsed_time:.2f} 秒\n")
        
        for test_name, result in results.items():
            status = "✓ 通過" if result else "✗ 失敗"
            print(f"  {status}: {test_name}")
        
        print("\n" + "="*60)
        if passed == total:
            print("✓ 所有測試通過！")
        else:
            print(f"✗ {total - passed} 個測試失敗")
        print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    # 檢查服務器是否運行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器")
        print(f"請確保 FastAPI 服務器正在運行: {BASE_URL}")
        print("\n運行以下命令啟動服務器:")
        print("  python3 fastapi_backend.py")
        sys.exit(1)
    
    # 運行測試
    tester = APITester(BASE_URL)
    tester.run_all_tests()
