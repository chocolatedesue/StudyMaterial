uv run clear_logs.py ./ospfv3_grid10x10_test/etc/ --yes

clab deploy -t ospfv3_grid10x10_test/ospfv3_grid10x10.clab.yaml

uv run setup/generate_ospfv3_functional.py grid 15 --yes

clab-ospfv3-grid10x10 

 --vertical-delay 2 --horizontal-delay 4

uv run auto.py clab-ospfv3-grid10x10 grid-prep --vertical-delay 5 --horizontal-delay 10 --yes

uv run setup/inject_functional.py  clab-ospfv3-grid10x10 --max-executions 2 -t link --min-interval 20 \
--max-interval 30 --specific-link 3,2-4,2 --execute 

uv run setup/inject.py  clab-ospfv3-grid10x10 --max-executions 2 -t link --min-interval 20 --max-interval 30 

uv run auto.py clab-ospfv3-grid10x10 grid-collect --yes

bash auto.sh clab-ospfv3-grid10x10 4

uv run setup/draw/converge_draw_10x10.py  ./data/converge-ospfv3_grid10x10.csv  ./results/converge-ospfv3_grid10x10.png

sudo ./.venv/bin/python3  clear_logs.py ./ospfv3_grid10x10_test/etc/ --yes