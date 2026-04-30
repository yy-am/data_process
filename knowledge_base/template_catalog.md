# Template Catalog

Each line below is one template entry used by the template-identification agent.
The agent must choose only from this catalog.

- templateCode: CUSTOMS_DECLARATION_STANDARD_CN | scene: customs | country: cn | headers: Declaration No || Declaration Date || Exporter || Importer || HS Code || Declared Value
- templateCode: ORDER_FULFILLMENT_STANDARD_JP | scene: fulfillment | country: jp | headers: Order ID || Order Date || Customer ID || Recipient Name || Delivery Postal Code || Delivery Address Line 1 || Delivery Address Line 2 || Contact Phone || SKU || Product Name || Quantity || Unit Price || Currency || Warehouse Code || Carrier || Tracking Number || Ship Date || Expected Arrival Date || Payment Method || Order Status || Sales Channel || Memo
- templateCode: PAYMENT_INVOICE_STANDARD_US | scene: payment | country: us | headers: Invoice No || Invoice Date || Buyer Name || Seller Name || Currency || Amount
- templateCode: CHANNEL_REBATE_STANDARD_MX | scene: rebate | country: mx | headers: Claim ID || Partner Name || Country || Program Name || Claim Period Start || Claim Period End || Invoice Reference || Product Family || Eligible Units || Rebate Rate || Rebate Amount || Currency || Approval Status || Approver || Approval Date || Cost Center || Tax ID || Bank Beneficiary || Bank Account || Bank Swift || Supporting Doc Ref || Internal Note
- templateCode: REBATE_MX_TEMPLATE | scene: rebate | country: mx | headers: Ticket || Distributor || Geo || Txn Curr || Total Back || Decision Dt
- templateCode: VENDOR_SETTLEMENT_STANDARD_EU | scene: settlement | country: eu | headers: Settlement No || Settlement Date || Vendor Name || Country || Net Amount || Tax Amount || Total Amount

