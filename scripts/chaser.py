import json
import pydot

class TxAnalyzer:
	def __init__(self, transaction_data_file_path):
		self.__transactions   = {}
		self.__searched_txids = {}
		self.__unspent_txids  = []

		self.load_transaction_data(transaction_data_file_path)

	def load_transaction_data(self, transaction_data_file_path):
		with open(transaction_data_file_path, 'r') as file:
			self.__transactions = json.load(file)

	@classmethod
	def get_terminate_txids(cls, graph_edges):
		input_txids  = list(set([graph_edge[0] for graph_edge in graph_edges]))
		output_txids = list(set([graph_edge[1] for graph_edge in graph_edges]))

		terminate_txids = []

		for output_txid in output_txids:
			if output_txid not in input_txids:
				terminate_txids.append(output_txid)

		return terminate_txids
	
	def get_next_root_txids(self, graph_edges):
		terminate_txids = TxAnalyzer.get_terminate_txids(graph_edges)

		next_root_txids = []

		for terminate_txid in terminate_txids:
			if terminate_txid not in self.__unspent_txids and terminate_txid not in self.__searched_txids:
				next_root_txids.append(terminate_txid)

		return next_root_txids

	def get_transaction(self, target_txid):
		if target_txid in self.__transactions.keys():
			return self.__transactions[target_txid]
		else:
			return {}

	def get_spent_transaction_ids(self, target_txid, ignore_pool_amount):
		spent_txids = []
		target_transaction = self.get_transaction(target_txid)

		# Check Invalid Transaction
		if len(target_transaction.keys()) == 0:
			return []

		# Search Spent Txids
		spent_value = 0
		unspent_value = 0
		for output in target_transaction['out']:
			if 'spent' in output.keys():
				spent_txids.append(output['spent'])
				spent_value += output['value']
			else:
				unspent_value += output['value']

		# If Target Transaction is Unspent 
		if len(spent_txids) == 0:
			if target_txid not in self.__unspent_txids:
				self.__unspent_txids.append(target_txid)
		elif unspent_value / 100000000.0 > ignore_pool_amount:
			if target_txid not in self.__unspent_txids:
				self.__unspent_txids.append(target_txid)

		return spent_txids

	def make_transaction_sub_graph(self, root_txids, max_graph_depth, sub_graph_number, ignore_pool_amount):
		search_target_txids = root_txids
		graph_edges = []

		# Search Depth Loop
		for search_depth in range(max_graph_depth):
			# Check Searching End
			if len(search_target_txids) == 0:
				break

			# One Depth Search Loop
			for search_target_txid in search_target_txids[:]:
				# Check Already Searched ?
				if search_target_txid in self.__searched_txids.keys():
					continue

				# Search Next Transactions
				spent_txids = self.get_spent_transaction_ids(search_target_txid, ignore_pool_amount)

				if len(spent_txids) == 0:
					if spent_txids not in self.__unspent_txids:
						self.__unspent_txids.append(search_target_txid)
				else:
					for spent_txid in spent_txids:
						search_target_txids.append(spent_txid)

						# Add Graph Edge
						graph_edges.append([search_target_txid, spent_txid])

				# Update Searching Status
				search_target_txids = list(set(search_target_txids))
				search_target_txids.remove(search_target_txid)
				self.__searched_txids[search_target_txid] = sub_graph_number

		# Add Remittance Amount Information
		for n,graph_edge in enumerate(graph_edges[:]):
			remittance_amount = 0
			target_transaction = self.get_transaction(graph_edge[1])

			for input_transaction in target_transaction['in']:
				if input_transaction['tx'] == graph_edge[0]:
					remittance_amount += float(input_transaction['value']) / 100000000.0 # 1 watanabe = 1.0

			graph_edges[n].append(remittance_amount)

		# Delete Duplicate Edge)
		graph_edges = list(map(list, set(map(tuple, graph_edges))))

		return graph_edges, self.__unspent_txids, root_txids

	def run_partial_analysis(self, root_txids, max_sub_graph_depth, max_sub_graph_number, attention_remittance_amount, ignore_pool_amount, analysis_name):
		for sub_graph_number in range(max_sub_graph_number):
			sub_graph_edges, unspent_txids, root_txids = self.make_transaction_sub_graph(root_txids, max_sub_graph_depth, sub_graph_number, ignore_pool_amount)
			searched_txids = self.__searched_txids
			terminate_txids = TxAnalyzer.get_terminate_txids(sub_graph_edges)

			# Make Files
			ResultFileMaker.make_dot_file(self.__transactions, sub_graph_edges, self.__unspent_txids, terminate_txids,root_txids, self.__searched_txids, attention_remittance_amount,analysis_name + '_transaction_graph_no' + str(sub_graph_number) + '.dot')
			ResultFileMaker.make_svg_file(analysis_name + '_transaction_graph_no' + str(sub_graph_number) + '.dot', analysis_name + '_transaction_graph_no' + str(sub_graph_number) + '.svg')

			# Update Root-Txids
			root_txids = self.get_next_root_txids(sub_graph_edges)

			# Check Analysis Finished
			print(sub_graph_number)
			if len(root_txids) == 0:
				break

		ResultFileMaker.make_unspent_txids_list(self.__unspent_txids, analysis_name + '_unspent_transactions.txt')

class ResultFileMaker:
	@classmethod
	def make_dot_file(cls, transactions, graph_edges, unspent_txids, terminate_txids, root_txids, searched_txids, attention_remittance_amount,output_path):
		# Header Data
		dot_file_data = 'digraph G{rankdir=TB;layout=dot;\n'

		# Node Data
		for root_txid in root_txids:
			if root_txid not in unspent_txids:
				node_data = '"' + root_txid + '" [style="solid,filled",color=red,fontcolor=white];\n'
				dot_file_data += node_data
			else:
				node_data = '"' + root_txid + '" [style="solid,filled",color=blue,fontcolor=white];\n'
				dot_file_data += node_data

		output_txids = list(set([graph_edge[1] for graph_edge in graph_edges]))

		for output_txid in output_txids:
			node_data = ''
			if output_txid in unspent_txids:
				node_data = '"' + output_txid + '" [style="solid,filled",color=blue,fontcolor=white];\n'
			elif output_txid in searched_txids.keys() and output_txid in terminate_txids:
				node_data = '"' + output_txid + '" [style="solid,filled",color=gray,fontcolor=black,label= "' + output_txid + ' to_Graph_No ' + str(searched_txids[output_txid]) + '"];\n'
			elif output_txid in terminate_txids:
				node_data = '"' + output_txid + '" [style="solid,filled",color=black,fontcolor=white];\n'


			dot_file_data += node_data

		# Edge Data
		for graph_edge in graph_edges:
			if graph_edge[2] > attention_remittance_amount:
				dot_file_data += '"' + graph_edge[0] + '" -> "' + graph_edge[1] + '" ' + '[label=' + str(graph_edge[2]) + ',arrowsize=2,color=firebrick1,penwidth=3]' +';\n'
			else:
				dot_file_data += '"' + graph_edge[0] + '" -> "' + graph_edge[1] + '" ' + '[label=' + str(graph_edge[2]) + ']' +';\n'

		# Footer Data
		dot_file_data += '}'

		with open(output_path,'w') as file:
			file.write(dot_file_data)

	@classmethod
	def make_svg_file(cls, dot_file_path, output_path):
		(graph,) = pydot.graph_from_dot_file(dot_file_path)
		graph.write_svg(output_path)

	@classmethod
	def make_unspent_txids_list(cls, unspent_txids, output_path):
		unspent_txids = list(set(unspent_txids))
		with open(output_path, 'w') as file:
			for unspent_txid in unspent_txids:
				file.write(unspent_txid + '\n')

if __name__ == '__main__':
	import sys

	transaction_data_file_path = sys.argv[1]
	root_txids_list_file_path = sys.argv[2]
	max_sub_graph_depth = int(sys.argv[3])
	max_sub_graph_number = int(sys.argv[4])
	attention_remittance_amount = float(sys.argv[5])
	ignore_pool_amount = float(sys.argv[6])
	output_name = sys.argv[7]

	tx_analyzer = TxAnalyzer(transaction_data_file_path)

	# Load Root Txids
	with open(root_txids_list_file_path, 'r') as file:
		root_txids = file.read().split('\n')

		while '' in root_txids:
			root_txids.remove('')

	tx_analyzer.run_partial_analysis(root_txids, max_sub_graph_depth, max_sub_graph_number, attention_remittance_amount, ignore_pool_amount, output_name)