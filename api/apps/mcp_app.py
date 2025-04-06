from flask import Blueprint, request, jsonify
from mcp.server.fastmcp import FastMCP
from rag.utils.es_conn import ESConnection
from api.utils.api_utils import get_json_result, get_data_error_result

mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/mcp')
mcp = FastMCP()

@mcp_bp.route('/search', methods=['POST'])
def es_search():
    """
    Elasticsearch搜索接口
    """
    try:
        data = request.get_json()
        index_name = data.get('index')
        query = data.get('query')
        
        if not index_name or not query:
            return get_data_error_result('Missing required parameters: index and query')
            
        es_conn = ESConnection()
        if not es_conn.indexExist(index_name):
            return get_data_error_result(f'Index {index_name} does not exist')
            
        # 执行搜索
        search = Search(using=es_conn.es, index=index_name)
        search = search.query('multi_match', query=query, fields=['content^3', 'title^2'])
        response = search.execute()
        
        results = []
        for hit in response:
            results.append({
                'id': hit.meta.id,
                'score': hit.meta.score,
                'title': getattr(hit, 'title', ''),
                'content': getattr(hit, 'content', '')
            })
            
        return get_json_result(data={
            'total': response.hits.total.value,
            'results': results
        })
        
    except Exception as e:
        return get_data_error_result(str(e))

@mcp_bp.route('/index', methods=['POST'])
def create_index():
    """
    创建ES索引
    """
    try:
        data = request.get_json()
        index_name = data.get('index')
        vector_size = data.get('vector_size', 1536)
        
        if not index_name:
            return get_data_error_result('Missing required parameter: index')
            
        es_conn = ESConnection()
        result = es_conn.createIdx(index_name, '', vector_size)
        
        return get_json_result(data={'success': bool(result)})
        
    except Exception as e:
        return get_data_error_result(str(e))

@mcp_bp.route('/index/<index_name>', methods=['DELETE'])
def delete_index(index_name):
    """
    删除ES索引
    """
    try:
        es_conn = ESConnection()
        es_conn.deleteIdx(index_name, '')
        return get_json_result(data={'success': True})
        
    except Exception as e:
        return get_data_error_result(str(e))

# 注册MCP路由
mcp.register_blueprint(mcp_bp) 