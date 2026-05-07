#!/bin/bash
#
#SBATCH --job-name=bench_gardener_luca_compress
#SBATCH --partition=any
#SBATCH --cpus-per-task=1
#SBATCH --output=slurm_logs/slurm_compress-%A_%a_stdout.log
#SBATCH --error=slurm_logs/slurm_compress-%A_%a_stderr.log
#SBATCH --ntasks=1

cd ~/PycharmProjects/aspframework/gardener/bench_gardener_luca
cd ..
srun tar czf bench_gardener_luca.tar.gz bench_gardener_luca