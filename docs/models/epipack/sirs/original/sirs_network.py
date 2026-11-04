from epipack import StochasticEpiModel
import networkx as nx

k0 = 50
R0 = 2.5
rho = 1
eta = R0 * rho / k0
omega = 1/14
N = int(1e4)
edges = [ (e[0], e[1], 1.0) for e in \
          nx.fast_gnp_random_graph(N,k0/(N-1)).edges() ]

SIRS = StochasticEpiModel(
            compartments=list('SIR'),
            N=N,
            edge_weight_tuples=edges
            )\
        .set_link_transmission_processes([
            ('I', 'S', eta, 'I', 'I'),
        ])\
        .set_node_transition_processes([
            ('I', rho, 'R'),
            ('R', omega, 'S'),
        ])\
        .set_random_initial_conditions({
                                        'S': N-100,
                                        'I': 100
                                       })
t_s, result_s = SIRS.simulate(40)
