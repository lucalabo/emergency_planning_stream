#!/bin/bash
#
#SBATCH --job-name=bench_gardener_luca_postprocess
#SBATCH --partition=any
#SBATCH --cpus-per-task=1
#SBATCH --output=slurm_logs/slurm_postprocess-%A_%a_stdout.log
#SBATCH --error=slurm_logs/slurm_postprocess-%A_%a_stderr.log
#SBATCH --ntasks=1

cd ~/PycharmProjects/aspframework/gardener/bench_gardener_luca
srun postprocess_results.py