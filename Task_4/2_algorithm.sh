#!/bin/bash

FASTQ_FILE=$1
REF_GENOME=$2
MAPPED_THRESHOLD=90

echo "Start"

fastqc $FASTQ_FILE -o .
mv "${FASTQ_FILE%.*}_fastqc.zip" "qc_report.zip"

bwa index $REF_GENOME
bwa mem $REF_GENOME $FASTQ_FILE > aligned.sam

samtools view -Sb aligned.sam > aligned.bam
samtools flagstat aligned.bam > flagstat.txt

MAPPED=$(grep -m 1 "mapped (" flagstat.txt | awk '{print$5}' | sed 's/[(%]//g')
echo "Mapped: $MAPPED%"

if (( $(echo "$MAPPED >= $MAPPED_THRESHOLD" | bc -l) )); then
    echo "OK"
else
    echo "NOT OK"
    exit 1
fi

samtools sort -o aligned_sorted.bam aligned.bam
samtools index aligned_sorted.bam

freebayes -f $REF_GENOME aligned_sorted.bam > variants.vcf

echo "Finish"
