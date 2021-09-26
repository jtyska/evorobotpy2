import os
from multiprocessing import Pool 
from datetime import date
my_experiments = open('../ini_generator/ini_list.txt')
experiments_list = my_experiments.readlines()

'''setting variables'''

''' type xx-yy where xx is the first item and yy the last one  '''
choosen_experiments = '0-59'

'''how many seeds do you want to run for each experiment?'''
number_of_seeds = 10

'''you can type the additional parameters that you want to use to run your experiments'''
additional_params = ''

'''how many experiments do you want to run simultaneously?'''
simultaneously = 96

'''seed initial number'''
initial_seed_number = 1


print("Welcome to the seed generator")
print("Showing available experiments \n")
for e in range(0, len(experiments_list)):
    print('{} - {}'.format(e, experiments_list[e].split(',')[0]))


if '-' in choosen_experiments:
    choosen_experiments = choosen_experiments.split('-')
    number_of_experiments = int(choosen_experiments[1]) - int(choosen_experiments[0])
    total_of_processes = number_of_experiments * int(number_of_seeds)

commands_list = []

for i in range(int(choosen_experiments[0]), int(choosen_experiments[1])+1):
    seed=initial_seed_number
    for n in range(0, int(number_of_seeds)):
        if '\n' in experiments_list[i]:
            experiments_list[i].replace("\n", "")
            experiments_list[i].replace(" ", "")
        data = experiments_list[i].split(',')
        find_folder = 'cd ../ini_generator/{}'.format(data[0])
        seed_command = 'python3 ../../bin/es.py -f {}'.format(data[1])
        seed_command = seed_command + (' -s {} {}'.format(seed, additional_params))
        new_command = [find_folder,seed_command]
        print(new_command)
        commands_list.append(new_command)
        seed+=1

def run_process(processo):
    os.system(processo[0]+'&&'+processo[1])


for i in range(0, int(total_of_processes), int(simultaneously)):                                                                          
    pool = Pool(processes=int(simultaneously))   
    if (i + simultaneously) > len(commands_list)-1:
        pool.map(run_process, commands_list[i:])
    else:                                                     
        pool.map(run_process, commands_list[i:(i+simultaneously)])
    print("{} seeds finished".format(simultaneously))


arquivo = open('seeds_{}.txt'.format(date.today()), 'a')
for command in commands_list:
    arquivo.write(command[1]+'\n')

arquivo.close()

 


