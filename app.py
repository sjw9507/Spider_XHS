# encoding: utf-8
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
    data = request.get_json()
    if not data or 'cookie' not in data or 'note_url' not in data:
        return error_response('missing required fields: cookie, note_url')
    cookie = data['cookie']
    note_url = data['note_url']
    success, msg, res_json = xhs_apis.get_note_info(note_url, cookie)
    if not success:
        return error_response(msg)
    try:
        note_data = res_json['data']['items'][0]
        note_data['url'] = note_url
        note_info = handle_note_info(note_data)
        return success_response(note_info)
    except Exception as e:
        return error_response(str(e))


@app.route('/api/user/notes', methods=['POST'])
def api_get_user_notes():
    data = request.get_json()
    if not data or 'cookie' not in data or 'user_url' not in data:
        return error_response('missing required fields: cookie, user_url')
    cookie = data['cookie']
    user_url = data['user_url']
    detail = data.get('detail', False)
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
            try:
                note_data = res_json['data']['items'][0]
                note_data['url'] = note_url
                detailed_notes.append(handle_note_info(note_data))
            except Exception as e:
                logger.warning(f'获取笔记详情失败: {e}')
    return success_response(detailed_notes)


@app.route('/api/note/search', methods=['POST'])
def api_search_note():
    data = request.get_json()
    if not data or 'cookie' not in data or 'query' not in data or 'require_num' not in data:
        return error_response('missing required fields: cookie, query, require_num')
    cookie = data['cookie']
    query = data['query']
    require_num = data['require_num']
    sort = data.get('sort', 0)
    note_type = data.get('note_type', 0)
    detail = data.get('detail', False)
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
            try:
                note_data = res_json['data']['items'][0]
                note_data['url'] = note_url
                detailed_notes.append(handle_note_info(note_data))
            except Exception as e:
                logger.warning(f'获取笔记详情失败: {e}')
    return success_response(detailed_notes)


@app.route('/api/note/comments', methods=['POST'])
def api_get_note_comments():
    data = request.get_json()
    if not data or 'cookie' not in data or 'note_url' not in data:
        return error_response('missing required fields: cookie, note_url')
    cookie = data['cookie']
    note_url = data['note_url']
    success, msg, comments = xhs_apis.get_note_all_comment(note_url, cookie)
    if not success:
        return error_response(msg)
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
    app.run(host='0.0.0.0', port=5000, debug=True)
