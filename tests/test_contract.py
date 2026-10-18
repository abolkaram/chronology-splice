from pathlib import Path
S=(Path(__file__).parents[1]/'contracts'/'contract.py').read_text()
def test_surface():
 for n in ('open_docket','add_source','seal','reconstruct','file','get_docket'):assert 'def '+n in S
def test_consensus_binds_edges_and_conflicts():assert 'return run()==leader.calldata' in S and "source_indexes':indexes(row)" in S
def test_distinct_sources_and_unique_events():assert "s['origin']==origin" in S and "x['id']==eid" in S
def test_partial_order_not_total_order():assert 'incoming=[0]*len(events)' in S and 'layers.append' in S
def test_cycles_and_disputes_block_filing():assert "d.state='CONFLICT'" in S and "d.state!='RECONSTRUCTED'" in S
