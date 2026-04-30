# Knowledge Base Index

This directory is the human-friendly view of the current POC knowledge base.

Current runtime template source:

- `template_catalog.md`

Each scene/country folder currently contains:

- the corresponding mapping rule JSON
- optional historical artifacts from earlier PoC stages

Current entries:

- `payment/us`
- `customs/cn`
- `settlement/eu`
- `fulfillment/jp`
- `rebate/mx`

Complex scenarios included:

- `fulfillment/jp`
  20+ columns, many logistics and address-related fields, with source/target field names not fully aligned.
- `rebate/mx`
  20+ columns, finance/rebate terminology with heavily different source/target labels such as `Ticket -> case_no` and `Distributor -> channel_partner`.

Test upload files are kept separately under:

- `sample_excels/input_files`
