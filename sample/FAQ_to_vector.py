import openai
import os
import pandas as pd
import numpy as np
import tiktoken
from pymongo import MongoClient
from starlette.config import Config
from langchain_openai import AzureOpenAIEmbeddings
import csv
import pprint

# .envファイルの読み込み
config = Config(".env")  
input_filename = "FAQ_sample.csv"

# # プロキシ設定
# # TSプロキシ
# proxy = f"http://${config('HTTP_PROXY_ACCOUNT')}:${config('HTTP_PROXY_PASSWORD')}@proxynatts.ac.toyotasystems.com:8081"
# os.environ["http_proxy"] = proxy
# os.environ["https_proxy"] = proxy
#-> vmだからいらない

# #AzureOpenAI　API設定
# openai.api_type = "azure"
# openai.azure_endpoint = config("OPENAI_API_RESOURCE_ENDPOINT")
# #openai.api_base = config("OPENAI_API_BASE")
# openai.api_version = config("OPENAI_API_VERSION")
# openai.api_key = config("OPENAI_API_KEY")
# openai.api_engine = config("OPENAI_API_ENGINE")

os.environ["AZURE_OPENAI_API_KEY"] = config("OPENAI_API_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = config("OPENAI_API_RESOURCE_ENDPOINT")
os.environ["AZURE_DEPLOYMENT"] = config("AZURE_DEPLOYMENT")
os.environ["OPENAI_API_VERSION"] = config("OPENAI_API_VERSION")
# os.environ["OPENAI_API_BASE"] = config("OPENAI_API_BASE")

#ベクトル化LLM
embeddings = AzureOpenAIEmbeddings(
   azure_deployment=os.environ["AZURE_DEPLOYMENT"],
   openai_api_version = os.environ["OPENAI_API_VERSION"]
)

#csvファイルの読み込み
df = pd.read_csv(input_filename)

#日本語になっている列名を変更
df = df.rename(columns={
   '問い合わせ文': 'Question',
   '応答文': 'Answer',
})

#列を結合し、新たな列を作成
# columns_to_combine = df.columns.difference(['Question','Answer'])
# df['combined'] = df[columns_to_combine].apply(lambda row: ','.join(row.values.astype(str)), axis=1)

#ベクトル化
# query_result = embeddings.embed_query(df['Question'])
df['vectorContent'] = embeddings.embed_documents(df['Question'])
print("Sample_vector_dim:" + str(len(df['vectorContent'][0])) + ":" + str(type(df['vectorContent'][0])))

# DataFrameをcsvファイルとして保存
try:
    df.to_csv('output.csv', index=False)
    print('■csvファイル作成完了')
except Exception as e:
    print('■csvファイルの作成に失敗しました')
    print('エラー内容:', e)

# model = "text-embedding-ada-002"
# # model_name = "yamaguchi-oaoi-ada2"

# def get_embedding(text, model=model):
#    text = text.replace("\n", " ")
#    # res = client.embeddings.create(
#    res = openai.embeddings.create(
#       input = text, 
#       model = "text-embedding-ada-002",
#       ).data[0].embedding
#    return res
#ベクトル化
# df['vectorContent'] = df['combined'].apply(lambda x: get_embedding(x))
#-> なんか動かん。理由なんだろ。

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

# MongoDBへの格納
try:
    for index, row in df.iterrows():
        doc = {
            'Question': row['Question'],
            'Answer': row['Answer'],
            'vectorContent': row['vectorContent'],
        }
        collection.insert_one(doc)
    print('■全てのデータの格納に成功しました')

except Exception as e:
    print('■データの格納に失敗しました')
    print('エラー内容:', e)


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

#ベクトル検索準備
# collection.create_index([("vectorContent", "cosmosSearch")])
message = "D.e-Connectで、自宅での共用PCから会社PCへ接続できない"
query_vector = embeddings.embed_documents(message)[0]
# print("Message_vector_dim:" + str(len(query_vector[0])) + ":" + str(type(query_vector)))

print(all(isinstance(i, (int, float)) for i in query_vector))
print(len(query_vector) > 0)

#ベクトル検索実行
try:
    results = vector_search(query_vector, 2)
    #出力
    for result in results:
        print(f"質問:{result['document']['Question']}")
        print(f"答え:{result['document']['Answer']}")
        print(f"類似度:{result['similarityScore']}")
except Exception as e:
    print(f"エラーが発生しました: {str(e)}")



