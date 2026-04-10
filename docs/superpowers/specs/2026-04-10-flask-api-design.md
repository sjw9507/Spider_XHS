# Flask API 接口服务设计

## 概述

将现有 Spider_XHS 爬虫项目以 Flask API 形式暴露，提供 4 个核心接口。不改动现有代码，仅新增 `app.py`。

## 技术选型

- **Web 框架**：Flask
- **数据处理**：复用 `xhs_utils/data_util.py` 中的处理函数
- **API 调用**：复用 `apis/xhs_pc_apis.py` 中的现有函数
- **无代理支持**，**无鉴权**

## 接口设计

所有接口使用 POST 方法，参数通过 JSON body 传递，cookie 在每次请求的 body 中传入。

### 1. 获取用户所有笔记

- **路径**：`POST /api/user/notes`
- **请求体**：

```json
{
  "cookie": "浏览器复制的cookie字符串",
  "user_url": "https://www.xiaohongshu.com/user/profile/xxx"
}
```

- **处理逻辑**：调用 `xhs_pc_apis.get_user_all_notes()`，用 `data_util.handle_note_info()` 加工每条笔记
- **返回**：加工后的笔记列表

### 2. 获取笔记信息

- **路径**：`POST /api/note/info`
- **请求体**：

```json
{
  "cookie": "cookie字符串",
  "note_url": "https://www.xiaohongshu.com/explore/xxx"
}
```

- **处理逻辑**：调用 `xhs_pc_apis.get_note_info()`，用 `data_util.handle_note_info()` 加工
- **返回**：加工后的笔记详情

### 3. 搜索笔记

- **路径**：`POST /api/note/search`
- **请求体**：

```json
{
  "cookie": "cookie字符串",
  "query": "搜索关键词",
  "require_num": 10,
  "sort": 0,
  "note_type": 0
}
```

- **参数说明**：
  - `query`：必填，搜索关键词
  - `require_num`：必填，需要获取的笔记数量
  - `sort`：可选，排序方式。0=综合(默认)，1=最新，2=最多点赞
  - `note_type`：可选，笔记类型。0=全部(默认)，1=视频，2=图文
- **处理逻辑**：调用 `xhs_pc_apis.search_some_note()`，用 `data_util.handle_note_info()` 加工
- **返回**：加工后的笔记列表

### 4. 获取笔记评论

- **路径**：`POST /api/note/comments`
- **请求体**：

```json
{
  "cookie": "cookie字符串",
  "note_url": "https://www.xiaohongshu.com/explore/xxx"
}
```

- **处理逻辑**：调用 `xhs_pc_apis.get_note_all_comment()`，用 `data_util.handle_comment_info()` 加工
- **返回**：加工后的评论列表（含子评论）

## 统一响应格式

成功：

```json
{
  "code": 0,
  "msg": "success",
  "data": { ... }
}
```

失败：

```json
{
  "code": -1,
  "msg": "错误信息",
  "data": null
}
```

## 文件结构

仅新增一个文件，不改动现有代码：

```
Spider_XHS/
├── app.py              # 新增：Flask 应用入口 + 4个路由
├── apis/               # 不改动
├── xhs_utils/          # 不改动
├── ...
```

## 启动方式

```bash
pip install flask
python app.py
```

默认监听 `0.0.0.0:5000`。
