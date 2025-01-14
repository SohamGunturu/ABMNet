#!/bin/bash
#SBATCH --time=0-20:10:00 
#SBATCH --job-name=ABMNet_GPU
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --output=./data/slurm_outputs/nl6_res_means%j.txt
#SBATCH --cpus-per-task=5
#SBATCH --gres=gpu:a100

python3 main.py -i 'data/static/NL6P.csv' --epochs 110 -h 128 -d 6 -o 'nl6_normalize_large' --gpu --normalize --normalize_out

#python3 main.py -i 'data/NL6_means.csv' -h 128 -d 5 -o 'nl6means_h128_d5.csv' --epochs 100 --normalize --type res_n --gpu

#python3 main.py -i 'data/gdag_1300ss_covs.csv' -h 128 --epochs 200 -d 20 -o 'gdag1300ss_large_norm' --gpu --normalize --type res_nn

#python3 main.py -i 'data/NL6_in.csv' -h 64 -d 10 -o 'nl6in' --epochs 200 --gpu

#python3 main.py -i 'data/NL6_means.csv' -h 512 -d 32 -o 'nl6means_large' --epochs 1000 --gpu --type res_nn --normalize
