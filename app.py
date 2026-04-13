# encoding: utf-8
import urllib.parse
from flask import Flask, request, jsonify
from loguru import logger
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.data_util import handle_note_info, handle_comment_info

app = Flask(__name__)
xhs_apis = XHS_Apis()


def success_response(data):
    return jsonify({"code": 0, "msg": "success", "data": data})


def error_response(msg):
    return jsonify({"code": -1, "msg": str(msg), "data": None})


@app.route('/api/note/info', methods=['POST'])
def api_get_note_info():
    """
    获取单篇笔记详情。
    Body:
      cookie (str, required)
      note_url (str, required) — 必须携带 xsec_token，建议带 xsec_source。
        格式: https://www.xiaohongshu.com/explore/{note_id}?xsec_token=XXX&xsec_source=pc_search
        xsec_source 可选值: pc_search / pc_user / pc_feed (默认 pc_search)
      raw (bool, optional) — true 返回原始 JSON
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'note_url' not in data:
        return error_response('missing required fields: cookie, note_url (note_url must carry xsec_token)')
    cookie = data['cookie']
    note_url = data['note_url']
    raw = data.get('raw', False)
    success, msg, res_json = xhs_apis.get_note_info(note_url, cookie)
    if not success:
        return error_response(msg)
    if raw:
        return success_response(res_json)
    try:
        note_data = res_json['data']['items'][0]
        note_data['url'] = note_url
        note_info = handle_note_info(note_data)
        return success_response(note_info)
    except Exception as e:
        return error_response(str(e))


@app.route('/api/user/notes', methods=['POST'])
def api_get_user_notes():
    """
    获取指定用户的全部笔记（自动翻页直到结束）。
    Body:
      cookie (str, required)
      user_url (str, required) — 必须携带 xsec_token，建议带 xsec_source。
        格式: https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token=XXX&xsec_source=pc_search
        xsec_source 缺省时内部默认为 pc_search
      detail (bool, optional) — true 则对每条笔记再调用详情接口
      raw (bool, optional) — detail=true 时，true 返回原始 JSON
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'user_url' not in data:
        return error_response('missing required fields: cookie, user_url (user_url must carry xsec_token)')
    cookie = data['cookie']
    user_url = data['user_url']
    detail = data.get('detail', False)
    raw = data.get('raw', False)
    success, msg, note_list = xhs_apis.get_user_all_notes(user_url, cookie)
    if not success:
        return error_response(msg)
    if not detail:
        return success_response(note_list)
    detailed_notes = []
    for note in note_list:
        note_url = f"https://www.xiaohongshu.com/explore/{note['note_id']}?xsec_token={note['xsec_token']}"
        s, m, res_json = xhs_apis.get_note_info(note_url, cookie)
        if s:
            if raw:
                detailed_notes.append(res_json)
                continue
            try:
                note_data = res_json['data']['items'][0]
                note_data['url'] = note_url
                detailed_notes.append(handle_note_info(note_data))
            except Exception as e:
                logger.warning(f'获取笔记详情失败: {e}')
    return success_response(detailed_notes)


@app.route('/api/user/notes/page', methods=['POST'])
def api_get_user_notes_page():
    """
    分页获取指定用户的笔记（由调用方控制翻页，单页固定 30 条）。
    Body:
      cookie (str, required)
      user_url (str, required) — 必须携带 xsec_token，建议带 xsec_source。
        格式: https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token=XXX&xsec_source=pc_search
        xsec_source 缺省时内部默认为 pc_search
      cursor (str, optional) — 首次请求传 "" 或省略；后续传上一次返回的 cursor
      raw (bool, optional) — true 返回原始 JSON
    Response data: { notes, has_more, cursor }
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'user_url' not in data:
        return error_response('missing required fields: cookie, user_url (user_url must carry xsec_token)')
    cookie = data['cookie']
    user_url = data['user_url']
    cursor = data.get('cursor', '')
    raw = data.get('raw', False)
    try:
        url_parse = urllib.parse.urlparse(user_url)
        user_id = url_parse.path.split('/')[-1]
        query_dict = dict(urllib.parse.parse_qsl(url_parse.query))
        xsec_token = query_dict.get('xsec_token', '')
        xsec_source = query_dict.get('xsec_source', 'pc_search')
    except Exception as e:
        return error_response(f'invalid user_url: {e}')
    success, msg, res_json = xhs_apis.get_user_note_info(user_id, cursor, cookie, xsec_token, xsec_source)
    if not success:
        return error_response(msg)
    if raw:
        return success_response(res_json)
    res_data = res_json.get('data', {})
    notes = res_data.get('notes', [])
    has_more = res_data.get('has_more', False)
    next_cursor = str(res_data.get('cursor', ''))
    return success_response({"notes": notes, "has_more": has_more, "cursor": next_cursor})


@app.route('/api/note/search', methods=['POST'])
def api_search_note():
    """
    关键词搜索笔记。
    Body:
      cookie (str, required)
      query (str, required) — 搜索关键词
      require_num (int, required) — 期望返回的笔记数量
      sort (int, optional) — 排序方式 0 综合 / 1 最新 / 2 最热 (默认 0)
      note_type (int, optional) — 笔记类型 0 全部 / 1 视频 / 2 图文 (默认 0)
      detail (bool, optional) — true 则对每条结果再拉详情
        (内部会用 note['xsec_token'] 拼出 explore URL)
      raw (bool, optional) — detail=true 时，true 返回原始 JSON
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'query' not in data or 'require_num' not in data:
        return error_response('missing required fields: cookie, query, require_num')
    cookie = data['cookie']
    query = data['query']
    require_num = data['require_num']
    sort = data.get('sort', 0)
    note_type = data.get('note_type', 0)
    detail = data.get('detail', False)
    raw = data.get('raw', False)
    success, msg, notes = xhs_apis.search_some_note(query, require_num, cookie, sort, note_type)
    if not success:
        return error_response(msg)
    notes = [n for n in notes if n.get('model_type') == 'note']
    if not detail:
        return success_response(notes)
    detailed_notes = []
    for note in notes:
        note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
        s, m, res_json = xhs_apis.get_note_info(note_url, cookie)
        if s:
            if raw:
                detailed_notes.append(res_json)
                continue
            try:
                note_data = res_json['data']['items'][0]
                note_data['url'] = note_url
                detailed_notes.append(handle_note_info(note_data))
            except Exception as e:
                logger.warning(f'获取笔记详情失败: {e}')
    return success_response(detailed_notes)


@app.route('/api/note/comments/page', methods=['POST'])
def api_get_note_comments_page():
    """
    分页获取单篇笔记的一级评论（由调用方控制翻页）。
    Body:
      cookie (str, required)
      note_id (str, required) — 笔记 ID（explore URL 路径最后一段）
      xsec_token (str, required) — 与该笔记关联的 xsec_token
      cursor (str, optional) — 首次传 "" 或省略；后续传上一次返回的 cursor
      raw (bool, optional) — true 返回原始 JSON
    Response data: { comments, has_more, cursor }
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'note_id' not in data or 'xsec_token' not in data:
        return error_response('missing required fields: cookie, note_id, xsec_token')
    cookie = data['cookie']
    note_id = data['note_id']
    xsec_token = data['xsec_token']
    cursor = data.get('cursor', '')
    raw = data.get('raw', False)
    success, msg, res_json = xhs_apis.get_note_out_comment(note_id, cursor, xsec_token, cookie)
    if not success:
        return error_response(msg)
    if raw:
        return success_response(res_json)
    note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"
    comments = res_json.get('data', {}).get('comments', [])
    result = []
    for comment in comments:
        comment['note_url'] = note_url
        result.append(handle_comment_info(comment))
    has_more = res_json.get('data', {}).get('has_more', False)
    next_cursor = res_json.get('data', {}).get('cursor', '')
    return success_response({"comments": result, "has_more": has_more, "cursor": next_cursor})


@app.route('/api/note/comments/top', methods=['POST'])
def api_get_note_top_comments():
    """
    获取单篇笔记的全部一级评论（自动翻页，不含子评论）。
    Body:
      cookie (str, required)
      note_id (str, required) — 笔记 ID（explore URL 路径最后一段）
      xsec_token (str, required) — 与该笔记关联的 xsec_token
      raw (bool, optional) — true 返回原始列表
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'note_id' not in data or 'xsec_token' not in data:
        return error_response('missing required fields: cookie, note_id, xsec_token')
    cookie = data['cookie']
    note_id = data['note_id']
    xsec_token = data['xsec_token']
    raw = data.get('raw', False)
    success, msg, comments = xhs_apis.get_note_all_out_comment(note_id, xsec_token, cookie)
    if not success:
        return error_response(msg)
    if raw:
        return success_response(comments)
    note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"
    result = []
    for comment in comments:
        comment['note_url'] = note_url
        result.append(handle_comment_info(comment))
    return success_response(result)


@app.route('/api/note/comments/all', methods=['POST'])
def api_get_note_all_comments():
    """
    获取单篇笔记的全部评论（含子评论，自动翻页）。
    Body:
      cookie (str, required)
      note_url (str, required) — 必须携带 xsec_token。
        格式: https://www.xiaohongshu.com/explore/{note_id}?xsec_token=XXX
        (本接口内部只解析 xsec_token，xsec_source 不使用)
      raw (bool, optional) — true 返回原始列表
    """
    data = request.get_json()
    if not data or 'cookie' not in data or 'note_url' not in data:
        return error_response('missing required fields: cookie, note_url (note_url must carry xsec_token)')
    cookie = data['cookie']
    note_url = data['note_url']
    raw = data.get('raw', False)
    success, msg, comments = xhs_apis.get_note_all_comment(note_url, cookie)
    if not success:
        return error_response(msg)
    if raw:
        return success_response(comments)
    result = []
    for comment in comments:
        comment['note_url'] = note_url
        comment_info = handle_comment_info(comment)
        sub_comments = []
        for sub in comment.get('sub_comments', []):
            sub['note_url'] = note_url
            sub_comments.append(handle_comment_info(sub))
        comment_info['sub_comments'] = sub_comments
        result.append(comment_info)
    return success_response(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
