# MonaChaser
![screenshot from 2018-09-12 12-33-19](https://user-images.githubusercontent.com/36693422/45400696-1c376500-b688-11e8-8745-0f9cc4bdaf53.png)
モナコインの汚染トランザクションをすべて追跡します。  
＊現在Outputsには1.0mona以下のプールを無視した場合の出力結果が入っています。

### Useage
`python scripts/chaser.py [transaction_json_file] [root_txids_list_file] [max_sub_graph_depth] [max_sub_graph_number] [attention_remittance_amount] [ignore_pool_amount] [output_name]`  
* tansaction_json_file : トランザクションデータをまとめたファイルのパス
* root_txids_list_file : 始点となるトランザクションのIDリストをまとめたファイルのパス
* max_sub_graph_depth : サブグラフの最大探索階層
* max_sub_graph_number : サブグラフの最大個数
* attention_remittance_amount : 送金量いくら以上のを注目するか
* ignore_pool_amount : 無視するプール量
* output_name : 解析結果ファイルの頭につける文字列（ディレクトリも指定可）

Example  
`python scripts/chaser.py data/MONA_Transactions.json data/root_txids_list.txt 15 300 10000 1.0 ./Outputs/monappy_occurrence_to_0907_depth15`

＊全未使用トランザクションを取得したいときは attention_remittance_amountを0に設定する。

### How To View
出力されるグラフの見方は以下の通り  

* 青ノード ： コインがPoolされている
* 赤ノード ： グラフの探索をするときの始点
* 黒ノード ： 探索限界
* 灰ノード ： 既に探索を別のサブグラフで行っている。末尾にサブグラフの番号がある。
* 赤エッジ：attention_remittance_amount以上の送金が行われている場合

### License
CC-BY-NC

### Author
@GuriTech (https://twitter.com/GuriTech)
