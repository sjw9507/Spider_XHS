# Spider_XHS Flask 接口实测示例（raw=true）

> 实测时间：2026-04-13
> 服务地址：`http://127.0.0.1:5000`
> 三个接口请求时均传 `raw=true`。所有接口外层统一返回 `{ code, msg, data }`：`code=0` 表示成功，失败时 `code=-1`、`data=null`。
> 下方 JSON 已精简（仅保留每类对象的 1–2 条代表数据），原始完整响应另存于 `tmp_api_results.json`（临时文件）。
>
> ⚠️ **关于 `raw` 字段的统一说明**：三个接口在 `raw=true` 时都直接返回**小红书原始 API JSON**，外层多一层 `success/code/msg/data` 包装。`raw=false`（默认）时 Flask 会做轻量整形，把翻页字段提到 `data` 顶层，方便直接消费。

---

## 1. `POST /api/user/notes/page` — 分页获取用户笔记

由调用方自己控制翻页，单页固定 30 条（底层 `xhs_apis.get_user_note_info` 的 `num=30`）。

### 请求
```http
POST /api/user/notes/page
Content-Type: application/json
```
```json
{
  "cookie": "<你的 cookie 字符串>",
  "user_url": "https://www.xiaohongshu.com/user/profile/64c3f392000000002b009e45?xsec_token=AB-GhAToFu07JwNk_AMICHnp7bSTjVz2beVIDBwSyPwvM=&xsec_source=pc_feed",
  "cursor": "",
  "raw": true
}
```

**字段说明**
| 字段 | 必填 | 说明 |
|---|---|---|
| `cookie` | 是 | 登录后的 xhs cookie 字符串 |
| `user_url` | 是 | **必须携带 `xsec_token`**，建议带 `xsec_source`（`pc_search` / `pc_user` / `pc_feed`，缺省时内部默认 `pc_search`） |
| `cursor` | 否 | 首次传 `""` 或省略；后续传上一次响应里 `data.data.cursor` |
| `raw` | 否 | `true` 时直接返回小红书原始 API JSON（外层多一层 `success/code/msg/data` 包装） |

### 响应（实测精简，raw=true）
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "success": true,
    "code": 0,
    "msg": "成功",
    "data": {
      "notes": [
        {
          "note_id": "683fe17f0000000023017c6a",
          "type": "normal",
          "display_title": "魔法师小龙从飞书来到小红书～",
          "xsec_token": "AB0EWIRcKfmGjNlTST8n7gAGSrR9NSqZY_eaLv6hjb7Ug=",
          "cover": {
            "file_id": "",
            "url": "",
            "trace_id": "",
            "width": 1242,
            "height": 1656,
            "url_default": "http://sns-webpic-qc.xhscdn.com/.../spectrum/1040g0k031ia280jrmq00...!nc_n_webp_mw_1",
            "url_pre": "http://sns-webpic-qc.xhscdn.com/.../spectrum/1040g0k031ia280jrmq00...!nc_n_webp_prv_1",
            "info_list": [
              {"image_scene": "WB_PRV", "url": "..."},
              {"image_scene": "WB_DFT", "url": "..."}
            ]
          },
          "interact_info": {
            "liked": false,
            "liked_count": "928",
            "sticky": true
          },
          "user": {
            "user_id": "64c3f392000000002b009e45",
            "nickname": "魔法师盖瑞",
            "nick_name": "魔法师盖瑞",
            "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31hdu5jc2jo5g5p63ue9ap7i5lt5h22g"
          }
        },
        {
          "note_id": "6898e8cc0000000025023042",
          "type": "normal",
          "display_title": "办公斗图神器！一键传送你最喜欢的表情包！",
          "xsec_token": "ABdVJQz02JJpzefrQdFxKtcq0amn_UNhKNbmlEqjPezUE=",
          "interact_info": {"liked": false, "liked_count": "61", "sticky": true},
          "user": {"user_id": "64c3f392000000002b009e45", "nickname": "魔法师盖瑞"}
        }
      ],
      "has_more": false,
      "cursor": ""
    }
  }
}
```

**字段路径说明**
- 翻页字段在 **`data.data.has_more` / `data.data.cursor`**（外层 Flask 包装 + 内层小红书原 JSON）
- `data.data.notes[]`：当前页笔记（实测共 13 条，已全部返回）
  - `note_id` + `xsec_token` 拼 explore URL：`https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}`
  - `type`：`normal`（图文）/ `video`
  - `interact_info.sticky`：是否置顶
- `has_more=true` 时把 `cursor` 透传到下次请求

---

## 2. `POST /api/note/search` — 关键词搜索笔记（单页）

底层调用 `xhs_apis.search_note`，**单页返回**，由调用方自己控制翻页（不再自动拉满 `require_num`）。

### 请求
```http
POST /api/note/search
Content-Type: application/json
```
```json
{
  "cookie": "<你的 cookie 字符串>",
  "query": "美食",
  "page": 1,
  "sort": 0,
  "note_type": 0,
  "note_time": 0,
  "note_range": 0,
  "pos_distance": 0,
  "geo": "",
  "raw": true
}
```

**字段说明**
| 字段 | 必填 | 说明 |
|---|---|---|
| `cookie` | 是 | 登录后的 xhs cookie 字符串 |
| `query` | 是 | 搜索关键词 |
| `page` | 否 | 页码，默认 1；想翻页就递增（小红书页大小约 20） |
| `sort` | 否 | 排序：0 综合 / 1 最新 / 2 最多点赞 / 3 最多评论 / 4 最多收藏（默认 0） |
| `note_type` | 否 | 0 全部 / 1 视频 / 2 图文（默认 0） |
| `note_time` | 否 | 发布时间：0 不限 / 1 一天内 / 2 一周内 / 3 半年内（默认 0） |
| `note_range` | 否 | 笔记范围：0 不限 / 1 已看过 / 2 未看过 / 3 已关注（默认 0） |
| `pos_distance` | 否 | 位置距离：0 不限 / 1 同城 / 2 附近（默认 0；非 0 时必须同时传 `geo`） |
| `geo` | 否 | 地理位置对象，`pos_distance` 非 0 时必填，会被序列化为 JSON 透传 |
| `raw` | 否 | `true` 时返回小红书原始 API JSON（外层多一层 `success/code/msg/data` 包装） |

### 响应（raw=true，单条 item 示例）
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "success": true,
    "code": 0,
    "msg": "成功",
    "data": {
      "items": [
        {
          "id": "69c4b106000000002003a15b",
          "model_type": "note",
          "xsec_token": "ABYWEisRlB3NUzLrxnV1cMVfwQywNtYQ-9RW2GMJ-uNI4=",
          "note_card": {
            "type": "video",
            "display_title": "春天要多吃的十道时令家常菜‼️",
            "corner_tag_info": [
              {"text": "03-26", "type": "publish_time"}
            ],
            "cover": {
              "width": 1080,
              "height": 1920,
              "url_default": "http://sns-webpic-qc.xhscdn.com/.../1040g00831u5ombgbia70...!nc_n_webp_mw_1",
              "url_pre": "http://sns-webpic-qc.xhscdn.com/.../1040g00831u5ombgbia70...!nc_n_webp_prv_1"
            },
            "image_list": [
              {
                "width": 1080,
                "height": 1920,
                "info_list": [
                  {"image_scene": "WB_DFT", "url": "..."},
                  {"image_scene": "WB_PRV", "url": "..."}
                ]
              }
            ],
            "interact_info": {
              "liked": false,
              "liked_count": "1049",
              "collected": false,
              "collected_count": "811",
              "comment_count": "7",
              "shared_count": "493"
            },
            "user": {
              "user_id": "625520e80000000010008699",
              "nickname": "厨神妈妈的美食日记",
              "nick_name": "厨神妈妈的美食日记",
              "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31fmrk4pt046g5oil43k411kp5mkg7l0?imageView2/2/w/80/format/jpg",
              "xsec_token": "ABRLufjWQ2BD-6Uj2CwWdjjqwwGG3LmqWQAXf1Xf8laYA="
            }
          }
        }
      ],
      "has_more": true
    }
  }
}
```

> raw 模式下原始 items 中可能混有非 note 的推广位（`model_type != 'note'`），需要自行过滤；`raw=false` 模式下 Flask 已自动过滤。

### 响应（raw=false，整形后）
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "notes": [
      {"id": "...", "model_type": "note", "xsec_token": "...", "note_card": {"...": "..."}}
    ],
    "has_more": true
  }
}
```

**字段路径说明**
| 字段 | raw=true（原生） | raw=false（整形后） |
|---|---|---|
| 列表 | `data.data.items[]`（含非 note 推广位） | `data.notes[]`（已过滤 `model_type=='note'`） |
| 是否还有下一页 | `data.data.has_more` | `data.has_more` |

- item 顶层 `id` + `xsec_token` → 笔记的 `note_id` / `xsec_token`，可直接喂给 `/api/note/comments/page`
- `note_card.user.user_id` + `note_card.user.xsec_token` → 作者的 `user_id` 和**用户级 `xsec_token`**，可拼 `user_url` 喂给 `/api/user/notes/page`
- `note_card.type`：`normal`（图文）/ `video`
- `note_card.interact_info` 各 count 都是字符串数字
- 翻页：`has_more=true` 时把请求里的 `page` 加 1 再请求

---

## 3. `POST /api/note/comments/page` — 分页获取笔记一级评论

由调用方自己控制翻页。

### 请求
```http
POST /api/note/comments/page
Content-Type: application/json
```
```json
{
  "cookie": "<你的 cookie 字符串>",
  "note_id": "69c4b106000000002003a15b",
  "xsec_token": "ABYWEisRlB3NUzLrxnV1cMVfwQywNtYQ-9RW2GMJ-uNI4=",
  "cursor": "",
  "raw": true
}
```

**字段说明**
| 字段 | 必填 | 说明 |
|---|---|---|
| `cookie` | 是 | 登录后的 xhs cookie 字符串 |
| `note_id` | 是 | 笔记 ID（explore URL 路径最后一段） |
| `xsec_token` | 是 | 与该笔记关联的 `xsec_token`（搜索/用户笔记接口里返回的那一个） |
| `cursor` | 否 | 首次传 `""` 或省略；后续传上一次响应里 `data.data.cursor` |
| `raw` | 否 | `true` 时返回小红书原始 API JSON（外层多一层 `success/code/msg/data` 包装） |

### 响应（实测精简，raw=true，本次返回 7 条评论）
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "success": true,
    "code": 0,
    "msg": "成功",
    "data": {
      "comments": [
        {
          "id": "69dc4a8d00000000350120e3",
          "note_id": "69c4b106000000002003a15b",
          "content": "很赞👍👍👍👍",
          "create_time": 1776044686000,
          "ip_location": "重庆",
          "like_count": "1",
          "liked": false,
          "status": 0,
          "show_tags": [],
          "at_users": [],
          "pictures": [],
          "sub_comment_count": "0",
          "sub_comment_cursor": "",
          "sub_comment_has_more": false,
          "sub_comments": [],
          "user_info": {
            "user_id": "5db6fbcc0000000001000503",
            "nickname": "张阿姨美食记",
            "image": "https://sns-avatar-qc.xhscdn.com/avatar/648ef68e0bc37647b1a9b81c.jpg?imageView2/2/w/120/format/jpg",
            "xsec_token": "ABxz_zJ-ZD4mqOA2YYF2d7jyh6ZVY5-nYXG7a_bBI8OzY=",
            "ai_agent": false
          }
        },
        {
          "id": "69d1af280000000014031ac2",
          "note_id": "69c4b106000000002003a15b",
          "content": "芦笋炒口蘑，香椿伴豆腐，香椿炒鸡蛋焯水，油焖笋，炒猪肝韭菜，鲫鱼，汤清炒桐高  黄豆芽炒肉末  腊肉炒蒜苗叶  春笋炒五花肉",
          "create_time": 1775349544000,
          "ip_location": "北京",
          "like_count": "1",
          "liked": false,
          "sub_comments": [],
          "user_info": {
            "user_id": "623596ae0000000010007370",
            "nickname": "平平安安",
            "image": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31gk4u9bk3i5g5ohliqn40srgs7njsro?imageView2/2/w/120/format/jpg",
            "xsec_token": "ABvsTKGyHZpgc2u-8VJZMl9vmjOdpK8grb9ZQEJbzpbgo="
          }
        }
      ],
      "cursor": "69c7eb250000000002037d23",
      "has_more": false,
      "time": 1776074860555,
      "user_id": "68ee0cf70000000032015a8b",
      "xsec_token": "ABH2r7yQ0WRzCrtQGJ9RUIns78syPlDxmQJNaWHelr9SA="
    }
  }
}
```

**字段路径说明（raw=true 与 raw=false 字段差异）**
| 字段 | raw=true（原生） | raw=false（加工后） |
|---|---|---|
| 翻页 | `data.data.has_more` / `data.data.cursor` | `data.has_more` / `data.cursor` |
| 评论 ID | `id` | `comment_id` |
| 评论时间 | `create_time`（epoch 毫秒） | `upload_time`（`YYYY-MM-DD HH:MM:SS`） |
| 评论者昵称 | `user_info.nickname` | `nickname` |
| 评论者头像 | `user_info.image` | `avatar` |
| 评论者 ID | `user_info.user_id` | `user_id` |
| 子评论 | `sub_comments[]`（同结构、嵌套） | 不返回（请走 `/api/note/comments/all`） |
| 子评论计数 | `sub_comment_count` / `sub_comment_has_more` | 不返回 |
| 评论附图 | `pictures[]` | `pictures[]` |
| 评论 IP | `ip_location` | `ip_location` |

- raw 模式下 `data.data` 还附带：`time`（服务端时间戳）、`user_id` / `xsec_token`（**当前登录账号**自身信息，非评论者）
- `has_more=true` 时透传 `data.data.cursor` 到下次请求即可继续翻页

---

## 级联调用示例

典型串联流程（对应上面 3 个接口的依赖关系）：

```
[1] 搜索:  /api/note/search  (query, page)
        ↓ raw=false: data.notes[i].id + data.notes[i].xsec_token       → note_id / 笔记 xsec_token
        ↓           data.notes[i].note_card.user.user_id + .xsec_token → user_id / 用户 xsec_token
        ↓ has_more=true 时把 page+1 再请求继续翻页
[2] 评论:  /api/note/comments/page  (note_id, xsec_token, cursor)
        ↓ has_more=true 时把上次返回的 cursor 透传到下次
[3] 用户笔记:  /api/user/notes/page  (user_url, cursor)
        user_url = https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={user_xsec}&xsec_source=pc_search
        ↓ has_more=true 时把上次返回的 cursor 透传到下次
```
