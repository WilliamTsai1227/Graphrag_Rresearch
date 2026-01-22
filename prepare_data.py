#!/usr/bin/env python3
"""
準備金融業數據用於 GraphRAG 索引
將 CSV 文件轉換為結構化文本格式
"""

import csv
import json
from pathlib import Path

def csv_to_text(csv_file, output_file):
    """將 CSV 文件轉換為文本格式"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    return rows

def create_structured_documents():
    """創建結構化的金融業文檔"""
    
    # 讀取 CSV 文件
    customers = csv_to_text('customers.csv', None)
    products = csv_to_text('loan_products.csv', None)
    applications = csv_to_text('loan_applications.csv', None)
    policies = csv_to_text('policies.csv', None)
    
    # 創建結構化文檔
    structured_docs = []
    
    # 1. 客戶文檔
    print("=== 客戶信息 ===")
    for customer in customers:
        doc = f"""
客戶 ID: {customer['customer_id']}
客戶名稱: {customer['customer_name']}
客戶類型: {customer['customer_type']}
信用評分: {customer['credit_score']}
年收入: {customer['annual_income']} 元
行業: {customer['industry']}
風險等級: {customer['risk_level']}

客戶 {customer['customer_name']} 是一位 {customer['customer_type']}，在 {customer['industry']} 行業工作。
該客戶的信用評分為 {customer['credit_score']} 分，年收入為 {customer['annual_income']} 元。
根據評估，該客戶被分類為 {customer['risk_level']}。
"""
        structured_docs.append(doc)
        print(f"客戶 {customer['customer_name']}: 信用評分 {customer['credit_score']}, 年收入 {customer['annual_income']}")
    
    # 2. 產品文檔
    print("\n=== 貸款產品 ===")
    for product in products:
        doc = f"""
產品 ID: {product['product_id']}
產品名稱: {product['product_name']}
產品類型: {product['product_type']}
利率: {product['interest_rate']}
貸款期限: {product['loan_term']}
最小金額: {product['min_amount']} 元
最大金額: {product['max_amount']} 元
最低信用評分要求: {product['min_credit_score']}
風險類別: {product['risk_category']}

{product['product_name']} 是銀行提供的 {product['product_type']} 產品。
該產品的利率為 {product['interest_rate']}，貸款期限為 {product['loan_term']} 個月。
最小貸款金額為 {product['min_amount']} 元，最大貸款金額為 {product['max_amount']} 元。
申請該產品的客戶信用評分必須達到 {product['min_credit_score']} 分以上。
該產品被分類為 {product['risk_category']}。
"""
        structured_docs.append(doc)
        print(f"產品 {product['product_name']}: 利率 {product['interest_rate']}, 最低信用評分 {product['min_credit_score']}")
    
    # 3. 申請文檔
    print("\n=== 貸款申請 ===")
    for app in applications:
        # 查找客戶和產品信息
        customer = next((c for c in customers if c['customer_id'] == app['customer_id']), None)
        product = next((p for p in products if p['product_id'] == app['product_id']), None)
        
        if customer and product:
            doc = f"""
申請 ID: {app['application_id']}
客戶: {customer['customer_name']} (ID: {app['customer_id']})
產品: {product['product_name']} (ID: {app['product_id']})
申請日期: {app['application_date']}
貸款金額: {app['loan_amount']} 元
批准狀態: {app['approval_status']}
批准原因: {app['approval_reason']}
提供利率: {app['interest_rate_offered']}

客戶 {customer['customer_name']} 於 {app['application_date']} 申請了 {product['product_name']}。
申請金額為 {app['loan_amount']} 元。
客戶的信用評分為 {customer['credit_score']} 分，年收入為 {customer['annual_income']} 元。
該產品的利率為 {product['interest_rate']}，最低信用評分要求為 {product['min_credit_score']} 分。
申請狀態為 {app['approval_status']}。
批准原因：{app['approval_reason']}。
"""
            structured_docs.append(doc)
            print(f"申請 {app['application_id']}: {customer['customer_name']} 申請 {product['product_name']}, 狀態: {app['approval_status']}")
    
    # 4. 政策文檔
    print("\n=== 風險管理政策 ===")
    for policy in policies:
        doc = f"""
政策 ID: {policy['policy_id']}
政策名稱: {policy['policy_name']}
政策類型: {policy['policy_type']}
描述: {policy['description']}
最低信用評分: {policy['min_credit_score']}
最大負債比例: {policy['max_debt_ratio']}
需要抵押品: {policy['collateral_required']}
監管要求: {policy['regulatory_requirement']}

{policy['policy_name']} 是銀行的 {policy['policy_type']} 政策。
該政策規定，申請相關貸款的客戶信用評分必須達到 {policy['min_credit_score']} 分以上（如適用）。
最大負債比例為 {policy['max_debt_ratio']}（如適用）。
是否需要抵押品：{policy['collateral_required']}。
該政策遵守 {policy['regulatory_requirement']} 的規定。
"""
        structured_docs.append(doc)
        print(f"政策 {policy['policy_name']}: {policy['policy_type']}")
    
    # 保存為文本文件
    with open('structured_documents.txt', 'w', encoding='utf-8') as f:
        for i, doc in enumerate(structured_docs, 1):
            f.write(f"=== 文檔 {i} ===\n")
            f.write(doc)
            f.write("\n" + "="*50 + "\n\n")
    
    print(f"\n✓ 已創建 {len(structured_docs)} 個結構化文檔")
    print("✓ 文檔已保存到 structured_documents.txt")
    
    # 創建 JSON 格式的元數據
    metadata = {
        "customers": customers,
        "products": products,
        "applications": applications,
        "policies": policies
    }
    
    with open('metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print("✓ 元數據已保存到 metadata.json")
    
    return structured_docs

if __name__ == "__main__":
    print("開始準備金融業數據...\n")
    create_structured_documents()
    print("\n數據準備完成！")
