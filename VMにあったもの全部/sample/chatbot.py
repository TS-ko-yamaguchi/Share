#設定
import openai
import os
import pandas as pd
import numpy as np
import tiktoken
from pymongo import MongoClient
from starlette.config import Config
from langchain_openai import AzureOpenAIEmbeddings
from flask import Flask, request, jsonify, render_template
app = Flask(__name__)

# .envファイルの読み込み
config = Config(".env")  
input_filename = "FAQ_sample.csv"

# #AzureOpenAI　API設定
os.environ["AZURE_OPENAI_API_KEY"] = config("OPENAI_API_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = config("OPENAI_API_RESOURCE_ENDPOINT")
os.environ["AZURE_DEPLOYMENT"] = config("AZURE_DEPLOYMENT")
os.environ["OPENAI_API_VERSION"] = config("OPENAI_API_VERSION")
# os.environ["OPENAI_API_BASE"] = config("OPENAI_API_BASE")

#DBへの接続
try:
    connection_string = config("MONGO_CONNECTION_STRING")
    client = MongoClient(connection_string)
    collection = client["doc"]["docs"]
    
    # データベースのリストを取得して、接続確認
    client.list_database_names()
    print('■DBへの接続成功')

except Exception as e:
    print('■DBへの接続に失敗しました')
    print('エラー内容:', e)

#ベクトル化LLM
embeddings = AzureOpenAIEmbeddings(
   # azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
   azure_deployment=os.environ["AZURE_DEPLOYMENT"],
   openai_api_version = os.environ["OPENAI_API_VERSION"]
)

#ベクトル検索（関数）
def vector_search(query_vector, num_results):
   #ベクトル検索
   search_query = {
      '$search': {
         "cosmosSearch": {
            "vector": query_vector, #検索ベクトル
            "path": "vectorContent", #ベクトルが格納されているフィールド
            "k": num_results  #類似スコア上位何件か
         },
         "returnStoredSource": True
      }
   } 
   #類似スコアも返却対象に
   project_stage = {
      '$project': {
         "similarityScore": {
            "$meta": "searchScore"
         },
         "document": "$$ROOT"
      }
   }
   results = collection.aggregate([search_query, project_stage])
   return results


#チャットボット
def open_ai_chat(message) -> str:
    query_vector = embeddings.embed_documents(message)[0]
    try:
        results = vector_search(query_vector, 1)
        #出力
        assistant_message = ",".join([result['document']['Answer'] for result in results])
       # print(f"検索結果: {assistant_message}")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")


    response = openai.chat.completions.create(
        model = "yamaguchi_oa", #deployment_name
        #検索結果をプロンプトに加える
        messages=[
            {"role": "system", "content": f"回答は{assistant_message}です。、の形式で絶対に返答するようにしてください。"},
            {"role": "user", "content": message}
        ],
        temperature=0,
   )
    return response.choices[0].message.content


message = "ユーザーのインプット"
ans = open_ai_chat("message")
#print(f"AIの回答:{ans}")

#エンドポイント
@app.route('/')
def home():
    return render_template('UI_chatbot.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.json['message']
    response = open_ai_chat(message)
    return jsonify({'response': response})

if __name__ == "__main__":
   #  app.run(port=5000, debug=True)
    app.run(port=5000)
