from __future__ import annotations

import random
from typing import List, Optional

import numpy as np
from qulacs import Observable, QuantumState
from qulacs.gate import RX, RZ
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler

from skqulacs.circuit import LearningCircuit
from skqulacs.circuit.pre_defined import create_qcl_ansatz


class QRCRegressor:
    def __init__(
        self,
        n_qubit: int,
        circuit: LearningCircuit,
        observables: List[Observable],
    ) -> None:
        self.n_qubit = n_qubit
        self.circuit = circuit
        self.observables = observables

    def fit(
        self,
        x_train: List[List[float]],
        y_train: List[float],
        maxiter: Optional[int] = None,
        generate_observables: bool = True,
        generate_circuit: bool = True,
        circuit_depth: int = 5,
        n_qubit: int = 8,
    ) -> None:
        self.x_scaler = MinMaxScaler()
        self.x_scaler.fit(x_train)
        x_train_scaled = self.x_scaler.transform(x_train)

        if generate_observables:
            self.observables = self.__create_observables()
        if generate_circuit:
            self.circuit = self.__create_random_circuit(n_qubit, circuit_depth)

        observation_results = self.__get_observation_results(x_train_scaled)
        self.regression = LinearRegression()
        self.regression.fit(observation_results, y_train)

    def predict(self, x_test: List[List[float]]) -> List[float]:
        x_test_scaled = self.x_scaler.transform(x_test)
        observation_results = self.__get_observation_results(x_test_scaled)
        ret_val: List[float] = self.regression.predict(observation_results)
        return ret_val

    def score(self, x_test: List[List[float]], y_test: List[float]) -> float:
        x_test_scaled = self.x_scaler.transform(x_test)
        observation_results = self.__get_observation_results(x_test_scaled)
        ret_val: float = self.regression.score(observation_results, y_test)
        return ret_val

    def __create_observables(self) -> List[Observable]:
        observables = list()
        for _ in range(80):
            observable = Observable(self.n_qubit)
            observable.add_random_operator(random.randint(2, 10))
            observables.append(observable)
        return observables

    def __get_observation_results(self, X: List[List[float]]) -> List[List[float]]:
        observation_results: List[List[float]] = list()

        for x in X:
            state = QuantumState(self.n_qubit)
            state.set_zero_state()
            for i in range(len(x)):
                if (i // self.n_qubit) % 2 == 0:
                    RX(i % self.n_qubit, x[i] * np.pi).update_quantum_state(state)
                else:
                    RZ(i % self.n_qubit, x[i] * np.pi).update_quantum_state(state)

            self.circuit._circuit.update_quantum_state(state)

            observation_results.append([
                observable.get_expectation_value(state)
                for observable in self.observables
            ])

        return observation_results

    def __create_random_circuit(self, n_qubit: int, c_depth: int) -> LearningCircuit:
        circuit = create_qcl_ansatz(n_qubit, c_depth, seed=0)
        return circuit
