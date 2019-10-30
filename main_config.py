import math
from functools import lru_cache
from pprint import pformat
import networkx as nx
import geneticlib
import time
import sndlib
import timer
import utils
import yen
import genetic.transponders as tconfiger
# import genetic.transponder_config as t_config
from geneticlib import Individual

net_name = 'abilene'
dat_source_prefix = 'usa'
net = sndlib.create_undirected_net(net_name, calculate_distance=True, calculate_reinforcement=True, calculate_ila=True)
net.load_demands_from_datfile('data/usa001.dat')

K = 3  # number of predefined paths
# predefined_paths = yen.ksp_all_nodes(net, nx.astar_path, heuristic_fun=dist, k=K)
# predefined_paths = get_kozdro_paths()
intensity = 0.01
intensity_str = f"{intensity}".replace(".", "")
predefined_paths = utils.get_predefined_paths(network_filename=f"data/sndlib/json/{net_name}/{net_name}.json",
                                              dat_filename=f"data/{dat_source_prefix}{intensity_str}.dat", npaths=K)

# demands = {key: DEMAND for key in predefined_paths}
# transponders_config = {DEMAND: t_config.create_config([(40, 4), (100, 4), (200, 8), (400, 12)], DEMAND, 3)}
t_config_file = 'data/transponder_configs_ip_5.json'
transponders_config = tconfiger.load_config(t_config_file)
demands = {key: math.ceil(value) for key, value in net.demands.items()}


@lru_cache(maxsize=1024)
def dist(a, b):
    return sndlib.calculate_haversine_distance_between_each_node(net)[a][b]


slices_usage = {
    0: 1,
    1: 1,
    2: 2,
    3: 3
}

b_cost = {
    0: 1,
    1: 2
}

transponders_cost = {
    (0, 0): 2,
    (1, 0): 5,
    (2, 0): 7,
    (3, 0): 9,
    (0, 1): 2.4,
    (1, 1): 6,
    (2, 1): 8.4,
    (3, 1): 11.8,
}

clock = timer.Clock()

bands = [(0, 191), (192, 383)]  # ranges of slices per band

OSNR = {
    0: 10,
    1: 15.85,
    2: 31.62,
    3: 158.49
}
e = 2.718
h = 6.62607004 * pow(10, -34)
freq = {
    0: 193800000000000.0,
    1: 188500000000000.0
}
l = {
    0: 0.046,
    1: 0.055
}
bandwidth = {
    0: 25000000000.0,
    1: 25000000000.0,
    2: 50000000000.0,
    3: 75000000000.0
}

V = 31.62
W = 31.62
P = 0.001

tools = geneticlib.Toolkit()
tools.set_fitness_weights(weights=(-1,))


def save_result(best_result: Individual, file_name: str):
    """
    demandy, użyte transpondery dla danego połączenia, stan sieci(slice`y)?
    suma użytych transponderów każdego typu
    :param best_chromosome:
    :param file_name
    :return:
    """
    best_chromosome = best_result.chromosome
    ndemands = len(best_chromosome.demands.values())
    structure = pformat(best_chromosome.genes, indent=1)
    total_transonders_used = [0 for _ in range(int(len(best_chromosome.transponders_cost.values()) / 2))]
    genes = best_chromosome.genes.values()
    for gene in genes:
        for subgene in gene:
            total_transonders_used[subgene[0]] += 1

    flatten_subgenes = [subgene for gene in genes for subgene in gene]
    sorted_subgenes = [subgene for subgene in sorted(flatten_subgenes, key=lambda x: x[2].value)]

    result = f"Number of demands: {ndemands}\n" \
        f"Cost: {best_result.values[0]}\n" \
        f"Transponders used: {total_transonders_used}\n" \
        f"Sorted paths: {sorted_subgenes}\n" \
        f"Power overflow: {best_chromosome.power_overflow} \n" \
        f"Slices overflow: {best_chromosome.slices_overflow}\n" \
        f"Transponders config: {t_config_file}\n" \
        f"Total time: {clock.time_elapsed()}\n" \
        f"Structure: {structure}\n"

    print(result)
    file_name = f"{file_name}_{time.time()}"

    with open(f'results/{file_name}', mode='w') as file:
        file.write(result)