#!/bin/bash
#
#SBATCH --job-name=bench_gardener_luca
#SBATCH --time=2:00:35
#SBATCH --partition=broadwell
#SBATCH --cpus-per-task=3
#SBATCH --mem-per-cpu=8534
#SBATCH --cpu-freq=2200000-2200000:performance
#SBATCH --output=slurm_logs/slurm-%A_%a_stdout.log
#SBATCH --error=slurm_logs/slurm-%A_%a_stderr.log

#SBATCH --array=1-60
#SBATCH --ntasks=1

cd ~/PycharmProjects/aspframework/gardener/bench_gardener_luca
start=$( awk "NR==$SLURM_ARRAY_TASK_ID" start_list.txt )
srun $start