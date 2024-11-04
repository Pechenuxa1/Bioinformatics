from toil.common import Toil
from toil.job import Job
import subprocess
import os


def run_command(command):
    subprocess.run(command, shell=True, check=True)


def run_fastqc(job, fastq_file):
    path, file = fastq_file.rsplit('/', 1)
    run_command(f"fastqc {fastq_file} -o {path}/")
    run_command(f"mv {path}/{file.rsplit('.', 1)[0]}_fastqc.zip {path}/qc_report.zip")


def index_reference_genome(job, reference_genome):
    run_command(f"bwa index {reference_genome}")


def align_reads(job, reference_genome, fastq_file):
    path, file = fastq_file.rsplit('/', 1)
    aligned_sam = f"{path}/aligned.sam"
    run_command(f"bwa mem {reference_genome} {fastq_file} > {aligned_sam}")
    return aligned_sam


def convert_to_bam(job, aligned_sam):
    path, file = aligned_sam.rsplit('/', 1)
    aligned_bam = f"{path}/aligned.bam"
    run_command(f"samtools view -Sb {aligned_sam} > {aligned_bam}")
    return aligned_bam


def alignment_statistics(job, aligned_bam, mapped_threshold):
    path, file = aligned_bam.rsplit('/', 1)
    flagstat_file = f"{path}/flagstat.txt"
    run_command(f"samtools flagstat {aligned_bam} > {flagstat_file}")

    with open(flagstat_file) as f:
        for line in f:
            if "mapped (" in line:
                percent_mapped = float(line.split()[4].strip("()%"))
                break

    print(f"Mapped: {percent_mapped}%")
    if percent_mapped >= mapped_threshold:
        print("OK")
    else:
        print("NOT OK")
        raise Exception()


def sort_and_index_bam(job, aligned_bam):
    path, file = aligned_bam.rsplit('/', 1)
    aligned_sorted_bam = f"{path}/aligned_sorted.bam"
    run_command(f"samtools sort -o {aligned_sorted_bam} {aligned_bam}")
    run_command(f"samtools index {aligned_sorted_bam}")
    return aligned_sorted_bam


def variant_calling(job, reference_genome, aligned_sorted_bam):
    path, file = reference_genome.rsplit('/', 1)
    variants_vcf = f"{path}/variants.vcf"
    run_command(f"freebayes -f {reference_genome} {aligned_sorted_bam} > {variants_vcf}")
    return variants_vcf


if __name__ == "__main__":

    MAPPED_THRESHOLD = 90

    parser = Job.Runner.getDefaultArgumentParser()
    parser.add_argument("fastq_file", type=str)
    parser.add_argument("ref_genome", type=str)
    options = parser.parse_args()
    options.logLevel = "INFO"
    options.clean = "never"

    FASTQ_FILE = options.fastq_file
    REF_GENOME = options.ref_genome

    with Toil(options) as toil:
       	print("Start")

        fastqc_run = Job.wrapJobFn(run_fastqc, FASTQ_FILE)

        index_ref = fastqc_run.addFollowOnJobFn(index_reference_genome, REF_GENOME)

        align_job = index_ref.addFollowOnJobFn(align_reads, REF_GENOME, FASTQ_FILE)

        bam_conversion = align_job.addFollowOnJobFn(convert_to_bam, align_job.rv())

        stats_job = bam_conversion.addFollowOnJobFn(alignment_statistics, bam_conversion.rv(), MAPPED_THRESHOLD)

        sort_index = stats_job.addFollowOnJobFn(sort_and_index_bam, align_job.rv())

        variants_job = sort_index.addFollowOnJobFn(variant_calling, REF_GENOME, sort_index.rv())

        toil.start(fastqc_run)

        print("Finish")
