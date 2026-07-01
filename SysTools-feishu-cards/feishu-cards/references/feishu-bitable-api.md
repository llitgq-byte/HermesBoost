# 飞书多维表格 API 参考

## 认证流程

### 获取 tenant_access_token

```python
import requests

app_id = "cli_xxxxxxxxxxxx"
app_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
response = requests.post(token_url, json={
    "app_id": app_id,
    "app_secret": app_secret
})
token = response.json()["tenant_access_token"]
```

## 多维表格操作

### 读取记录

```python
app_token = "XXXXXXXXXXXXXXXXXXXX"  # 从 URL 提取
 table_id = "tblXXXXXXXXXXXX"      # 表格 ID

headers = {"Authorization": f"Bearer {token}"}
records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
response = requests.get(records_url, headers=headers)
records = response.json()["data"]["items"]
```

### 新增记录

```python
new_record = {
    "fields": {
        "文本": "测试内容",
        "数字": 123,
        "日期": 1680000000000  # 时间戳（毫秒）
    }
}

response = requests.post(records_url, headers=headers, json=new_record)
```

### 更新记录

```python
record_id = "recXXXXXXXXXXXX"
update_url = f"{records_url}/{record_id}"

update_data = {
    "fields": {
        "文本": "更新后的内容"
    }
}

response = requests.put(update_url, headers=headers, json=update_data)
```

### 删除记录

```python
delete_url = f"{records_url}/{record_id}"
response = requests.delete(delete_url, headers=headers)
```

## 文档操作

### 读取文档元数据

```python
doc_token = "TigKdnp9roMHcUxU7t9cvQiHnTg"
meta_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
response = requests.get(meta_url, headers=headers)
```

### 读取文档块结构

```python
blocks_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
response = requests.get(blocks_url, headers=headers)
blocks = response.json()["data"]["items"]
```

### 插入文本块

```python
# 在页面块下创建子块
parent_block_id = doc_token  # 页面块 ID
children_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{parent_block_id}/children"

new_block = {
    "index": 0,
    "children": [
        {
            "block_type": 2,  # 文本块
            "text": {
                "elements": [
                    {
                        "text_run": {
                            "content": "自动写入的内容",
                            "text_element_style": {
                                "bold": True
                            }
                        }
                    }
                ],
                "style": {
                    "align": 1  # 居中
                }
            }
        }
    ]
}

response = requests.post(children_url, headers=headers, json=new_block)
```

## 权限申请清单

| 权限 | 用途 | 申请地址 |
|------|------|---------|
| `bitable:app` | 多维表格应用权限 | https://open.feishu.cn/app/{app_id}/auth |
| `bitable:app:readonly` | 只读权限 | 同上 |
| `base:table:read` | 读取表格 | 同上 |
| `base:record:retrieve` | 读取记录 | 同上 |
| `base:record:create` | 创建记录 | 同上 |
| `base:record:update` | 更新记录 | 同上 |
| `base:record:delete` | 删除记录 | 同上 |
| `docx:document:readonly` | 文档只读 | 同上 |
| `docx:document` | 文档读写 | 同上 |

## 常见错误

| 错误码 | 原因 | 解决 |
|--------|------|------|
| 99991663 | Token 无效 | 检查 app_id/app_secret |
| 99991672 | 权限不足 | 申请所需权限 |
| 99991661 | 文档不存在 | 检查 doc_token |
| 99991662 | 表格不存在 | 检查 app_token/table_id |

## 关键要点

1. **app_token** 从多维表格 URL 提取：`https://xxx.feishu.cn/base/{app_token}`
2. **table_id** 从表格设置中查看
3. **doc_token** 从文档 URL 提取：`https://xxx.feishu.cn/docx/{doc_token}`
4. 权限申请后需要**发布应用版本**并**管理员审批**
5. 文档/表格需要**添加应用**并授权"可编辑"

## 与 Hermes 集成

### 自动写入日报

```python
# 在 Cron 任务中调用
def write_daily_report(data):
    token = get_feishu_token()
    app_token = "XXXXXXXX"
    table_id = "tblXXXXXXXX"
    
    record = {
        "fields": {
            "日期": data["date"],
            "Agent": data["agent"],
            "会话数": data["sessions"],
            "工具调用": data["tools"],
            "错误数": data["errors"]
        }
    }
    
    requests.post(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers={"Authorization": f"Bearer {token}"},
        json=record
    )
```
