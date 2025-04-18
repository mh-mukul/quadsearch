import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sentence_transformers import SentenceTransformerTrainingArguments
from sentence_transformers.training_args import BatchSamplers

load_dotenv()
MODEL_DIR = os.environ.get("EMBEDDING_MODEL")

args = SentenceTransformerTrainingArguments(
    # output directory and hugging face model ID
    output_dir=MODEL_DIR,
    num_train_epochs=10,                         # number of epochs
    per_device_train_batch_size=5,             # train batch size
    gradient_accumulation_steps=16,             # for a global batch size of 512
    per_device_eval_batch_size=16,              # evaluation batch size
    warmup_ratio=0.1,                           # warmup ratio
    learning_rate=2e-5,                         # learning rate, 2e-5 is a good value
    # use constant learning rate scheduler
    lr_scheduler_type="cosine",
    optim="adamw_torch_fused",                  # use fused adamw optimizer
    tf32=False,                                  # use tf32 precision
    bf16=False,                                  # use bf16 precision
    # MultipleNegativesRankingLoss benefits from no duplicate samples in a batch
    batch_sampler=BatchSamplers.NO_DUPLICATES,
    eval_strategy="epoch",                      # evaluate after each epoch
    save_strategy="epoch",                      # save after each epoch
    logging_steps=10,                           # log every 10 steps
    save_total_limit=3,                         # save only the last 3 models
    # load the best model when training ends
    load_best_model_at_end=True,
    # Optimizing for the best ndcg@10 score for the 128 dimension
    metric_for_best_model="eval_dim_128_cosine_ndcg@10",
)


custom_encoder = SentenceTransformer(
    args.output_dir, device="cpu"
)
