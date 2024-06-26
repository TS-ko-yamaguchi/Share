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
#    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_DEPLOYMENT"],
    openai_api_version = os.environ["OPENAI_API_VERSION"]
)

#ベクトル検索の関数
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
def open_ai_chat(user_message, useAI) -> str:
    
    #ベクトル化
    query_vector = embeddings.embed_documents(user_message)[0]
    #検索
    try:
        results = vector_search(query_vector, 1)
        #出力
        assistant_message = ",".join([result['document']['Answer'] for result in results])
        print("検索成功")
        print(f"検索結果: {assistant_message}")
    except Exception as e:
        print("検索失敗")
        print(f"エラーが発生しました: {str(e)}")

    #生成AIによる回答生成
    if useAI:
        try:
            openai.api_type = "azure"
            response = openai.chat.completions.create(
                model = "yamaguchi_oa", #deployment_name
                #検索結果をプロンプトに加える
                messages=[
                    # {"role": "system", "content": f"[問い合わせ内容は「{user_message}」ですね。回答は{assistant_message}です。]と出力してください。出力は読みやすいように適宜改行をしてください。"},
                    {"role": "system", "content": f"「{assistant_message}」を読みやすく要約してください。出力は,愛着が湧くようにフレンドリーな回答にしてください。"},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
            )
            assistant_message = response.choices[0].message.content
            print("回答生成-成功")
        except Exception as e:
            print(f"回答生成-失敗: {str(e)}")
    #回答を返す       
    # return jsonify({'response': assistant_message})
    return assistant_message

@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.json['message']
    useAI = request.json.get('useAI', False) 
    response = open_ai_chat(message, useAI)
    return jsonify({'response': response})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
    # app.run(port=5000)