# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ts-tzsAsPsqNn2_8YAwAN5iFhxGdgRMr
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install gurobipy

import numpy as np  # importing numpy
from gurobipy import Model, GRB, quicksum
import random
import matplotlib.pyplot as plt
import json


class Job:
    def __init__(self, index, task_sequence, release_date, due_date, weight):
        self.index = index
        self.task_sequence = task_sequence
        self.release_date = release_date
        self.due_date = due_date
        self.weight = weight

    def show(self):
        print("Job with index {} task sequence {} release date {} due date {} weight {}\n".format(self.index,
                                                                                                  self.task_sequence,
                                                                                                  self.release_date,
                                                                                                  self.due_date,
                                                                                                  self.weight))


class Task:
    def __init__(self, index, processing_time, machines):
        self.index = index
        self.processing_time = processing_time
        self.machines = machines  # list of machine indices on which this task can be performed

    def show(self):
        print(
            'Task with index {} processing time {} and machines {}\n'.format(self.index, self.processing_time,
                                                                             self.machines))


class Instance:
    def __init__(self, nb_operators, alpha, beta, jobs, tasks, operators):
        self.nb_operators = nb_operators
        self.alpha = alpha  # unit penalty
        self.beta = beta  # tardiness
        self.jobs = jobs
        self.tasks = tasks
        self.operators = operators  # operators[i-1, m-1] = list of operators that can operate task i on machine m

    def nb_jobs(self):
        return len(self.jobs)

    def nb_tasks(self):
        return len(self.tasks)

    def nb_machines(self):
        return np.shape(self.operators)[1]

    def nb_operators(self):
        return self.nb_operators

    def show(self):
        print('Instance with {} operators, unit penalty {}, tadiness {} and \n'.format(self.nb_operators, self.alpha,
                                                                                       self.beta))
        print("Jobs : \n")
        for j in range(self.nb_jobs()):
            self.jobs[j].show()
        print("Tasks: \n")
        for t in range(self.nb_tasks()):
            self.tasks[t].show()
        print("Operators: \n")
        print(operators)


file = open("/Users/pierr/OneDrive/Documents/Pierre-Louis/Ponts/2A GI/Recherche "
            "opérationnelle/sujet_et_instances_projet_REOP22-23/sujet_et_instances_projet_REOP22-23/instances/KIRO"
            "-tiny.json")
data = json.load(file)

parameters_data = data["parameters"]
nb_tasks = parameters_data["size"]["nb_tasks"]
nb_machines = parameters_data["size"]["nb_machines"]
nb_operators = parameters_data["size"]["nb_operators"]
alpha = parameters_data["costs"]["unit_penalty"]
beta = parameters_data["costs"]["tardiness"]
jobs_data = data["jobs"]
jobs = [
    Job(job["job"],
        job["sequence"],
        job["release_date"],
        job["due_date"],
        job["weight"],
        ) for job in jobs_data
]

tasks_data = data["tasks"]
tasks = [
    Task(task["task"],
         task["processing_time"],
         [machine["machine"] for machine in task["machines"]],
         ) for task in tasks_data
]

operators = np.empty((nb_tasks, nb_machines), dtype=object)
for task in tasks_data:
    i = task["task"]
    for machine in task["machines"]:
        m = machine["machine"]
        operator_list = machine["operators"]
        operators[i - 1, m - 1] = operator_list

instance = Instance(nb_operators, alpha, beta, jobs, tasks, operators)


def PLNE2(nb_tasks):  # T le nb de tables; P la capacité par table; I le nb d'invités
    model= Model();
    # Définition des variables
    b = {}  # Starting time for a task
    m = {}  # Machine used for a task
    o = {}  # Operator used for a task
    c = {}  # Time at which task is completed
    B = {}  # Time at which job starts
    C = {}  # Time at which job is completed
    U = {}  # Unit of penalty
    T = {}  # Tardiness

    y={}    # 1 if task i is performed before task j
    x={}    # 1 if task i is performed on machine k
    z={}    # 1 if task i is performed on machine k with operator o

    for i in range(1,nb_tasks+1):
        # Par défaut lb=0 et ub=+infini
        b[i] = model.addVar(name="b" + str(i), vtype=GRB.INTEGER)  # Starting time for task i
        c[i] = model.addVar(name="c" + str(i), vtype=GRB.INTEGER)  # Finishing time for task i
        m[i] = model.addVar(name="m" + str(i), vtype=GRB.INTEGER)  # Machine used for task i
        o[i] = model.addVar(name="o" + str(i), vtype=GRB.INTEGER)  # Operator used for task i
        for j in range(i,nb_tasks+1):
            y[i,j]=model.addVar(name="y" + str(i) + str(j), vtype=GRB.BINARY) # 1 si tache i avant j


        for k in range(1,nb_machines+1):
            x[i, k] = model.addVar(name="x" + str(i) + str(k), vtype=GRB.BINARY) # 1 si la tache i est faite sur la machine k
            for l in range(nb_operators):
                z[i, k, l] = model.addVar(name="z" + str(i) + str(k) + str(l), vtype=GRB.BINARY)  # 1 si la tache i est faite sur la machine k



    for j in range(1,instance.nb_jobs()+1):
        B[j] = model.addVar(name="B" + str(j), vtype=GRB.INTEGER)  # Starting time for job i
        C[j] = model.addVar(name="x" + str(j), vtype=GRB.INTEGER)  # Finishing time of work j
        U[j] = model.addVar(name="x" + str(j), vtype=GRB.BINARY, lb=0, ub=1)  # Tardiness of job j
        T[j] = model.addVar(name="x" + str(j), vtype=GRB.INTEGER)  # Unit of penalty for job j


    # Fonction objectif
    model.setObjective(
        quicksum(
            jobs[j-1].weight * (C[j] + instance.alpha * U[j] + instance.beta * T[j]) for j in range(1,instance.nb_jobs()+1)),
        GRB.MINIMIZE)

    # Définition des contraintes
    # Contrainte 1
    for i in range(1, nb_tasks+1): #vérifiée
        model.addConstr(c[i] == (b[i] + instance.tasks[i-1].processing_time))

    # Contrainte 2
    for j in range(1, instance.nb_jobs()+1): #vérifiée
        model.addConstr(B[j] == b[instance.jobs[j-1].task_sequence[0]])

    # Contrainte 3
    for j in range(1,instance.nb_jobs()+1): #vérifiée
        model.addConstr(C[j] == c[instance.jobs[j-1].task_sequence[-1]])

    # Contrainte 4
    for j in range(1,instance.nb_jobs()+1): #vérifiée
        model.addConstr(B[j] >= instance.jobs[j-1].release_date)

    # Contrainte 5
    for j in range(1, instance.nb_jobs()+1): #vérifiée
        for i in range(len(instance.jobs[j-1].task_sequence)-1):
            model.addConstr((b[instance.jobs[j-1].task_sequence[i+1]]) >= c[instance.jobs[j-1].task_sequence[i]])

    # Contrainte 6
    M=1000000
    for j in range(1, instance.nb_jobs()+1):
        model.addConstr(T[j] >= C[j] - instance.jobs[j-1].due_date)
        model.addConstr(T[j] >= 0)
        model.addConstr(U[j] >= T[j]/M)
        model.addConstr(U[j] <= 1)

    model.optimize()

    # Contrainte 7
    #print('x',x)
    #print('y',y)
    for i in range(1,nb_tasks+1):
        for j in range(i,nb_tasks+1):
            for k in instance.tasks[i-1].machines:
                #print('i,j',(i,j))
                #print('i,k',(i,k))
                #print('j,k',(j,k))
                model.addConstr(c[i] - b[j] <= -M * (1 - y[i, j]) - M * (2 - x[i, k] - x[j, k]))
                model.addConstr((c[j] - b[i]) <= (-M * y[i, j] - M * (2 - x[i, k] - x[j, k])))


    #print('Obj: %g' % model.ObjVal)
    return('Obj: %g' % model.ObjVal)


PLNE2(nb_tasks)

'''
    # Contrainte chaque invité est à une table
    for i in range(I):
        m.addConstr(quicksum(x[i, k] for k in range(T)) == 1)
    # Contrainte de capacité des tables
    # Contrainte de parité
    # Contrainte de famille
    for k in range(T):
        m.addConstr(quicksum(x[i, k] for i in range(I)) <= P)
        m.addConstr(quicksum(T * x[i, k] * sexe[i] for i in range(I)) <= T + quicksum(sexe[i] for i in range(I)))
        m.addConstr(quicksum(T * x[i, k] * sexe[i] for i in range(I)) >= - T + quicksum(sexe[i] for i in range(I)))
        m.addConstr(quicksum(T * x[i, k] * famille[i] for i in range(I)) <= T + quicksum(famille[i] for i in range(I)))
        m.addConstr(
            quicksum(T * x[i, k] * famille[i] for i in range(I)) >= - T + quicksum(famille[i] for i in range(I)))
    # Lien entre y et x ?
    # entre z et x
    # entre w et x
    for i in range(I):
        for j in range(I):
            if i != j:
                for k in range(T):
                    # m.addConstr(y[i, j, k] <= (1/2)*(x[i, k]+x[j, k])*abs(sexe[i]-sexe[j]))
                    # m.addConstr(z[i, j, k] <= (1/2)*(x[i, k]+x[j, k])*abs(famille[i]-famille[j]))
                    m.addConstr(w[i, j, k] <= (1 / 2) * (x[i, k] + x[j, k]) * abs(couple[i][j]))
    m.optimize()
    table = []

    for v in x.values():
        if v.X == 1:
            lettre = v.VarName
            l = lettre[1:lettre.find(',')]
            for k in range(T):
                if int(lettre[lettre.find(',') + 1:]) == k:
                    for i in range(I):
                        if int(lettre[1:lettre.find(',')]) == i:
                            table.append([i, k])

    return table
'''''

'''
Exemple de code pour le projet TD log 
def PNLE(sexe, famille, couple, T, P, I):  # T le nb de tables; P la capacité par table; I le nb d'invités
    m = Model();
    # création des variables
    x = {}
    y = {}
    z = {}
    w = {}
    for i in range(I):
        for k in range(T):
            x[i, k] = m.addVar(name="x" + str(i) + "," + str(k), vtype=GRB.INTEGER, lb=0, ub=1)
            for j in range(I):
                y[i, j, k] = m.addVar(vtype=GRB.INTEGER, name="y" + str(i) + str(j) + str(k), lb=0, ub=1)
                z[i, j, k] = m.addVar(vtype=GRB.INTEGER, name="z" + str(i) + str(j) + str(k), lb=0, ub=1)
                w[i, j, k] = m.addVar(vtype=GRB.INTEGER, name="w" + str(i) + str(j) + str(k), lb=0, ub=1)
    # Fonction objectif
    m.setObjective(
        quicksum(y[i, j, k] + z[i, j, k] + 20 * w[i, j, k] for i in range(I) for j in range(I) for k in range(T)),
        GRB.MAXIMIZE)
    # Contrainte chaque invité est à une table
    for i in range(I):
        m.addConstr(quicksum(x[i, k] for k in range(T)) == 1)
    # Contrainte de capacité des tables
    # Contrainte de parité
    # Contrainte de famille
    for k in range(T):
        m.addConstr(quicksum(x[i, k] for i in range(I)) <= P)
        m.addConstr(quicksum(T * x[i, k] * sexe[i] for i in range(I)) <= T + quicksum(sexe[i] for i in range(I)))
        m.addConstr(quicksum(T * x[i, k] * sexe[i] for i in range(I)) >= - T + quicksum(sexe[i] for i in range(I)))
        m.addConstr(quicksum(T * x[i, k] * famille[i] for i in range(I)) <= T + quicksum(famille[i] for i in range(I)))
        m.addConstr(
            quicksum(T * x[i, k] * famille[i] for i in range(I)) >= - T + quicksum(famille[i] for i in range(I)))
    # Lien entre y et x ?
    # entre z et x
    # entre w et x
    for i in range(I):
        for j in range(I):
            if i != j:
                for k in range(T):
                    # m.addConstr(y[i, j, k] <= (1/2)*(x[i, k]+x[j, k])*abs(sexe[i]-sexe[j]))
                    # m.addConstr(z[i, j, k] <= (1/2)*(x[i, k]+x[j, k])*abs(famille[i]-famille[j]))
                    m.addConstr(w[i, j, k] <= (1 / 2) * (x[i, k] + x[j, k]) * abs(couple[i][j]))
    m.optimize()
    table = []

    for v in x.values():
        if v.X == 1:
            lettre = v.VarName
            l = lettre[1:lettre.find(',')]
            for k in range(T):
                if int(lettre[lettre.find(',') + 1:]) == k:
                    for i in range(I):
                        if int(lettre[1:lettre.find(',')]) == i:
                            table.append([i, k])

    return table
'''