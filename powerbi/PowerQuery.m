// Create one blank query for each block and use the indicated query name.
// Query: fact_order
let
 Source = Csv.Document(File.Contents("data/exports/fact_order.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
 Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
 Types = Table.TransformColumnTypes(Headers, {
  {"order_id", type text}, {"customer_id", type text}, {"customer_state", type text}, {"order_status", type text},
  {"order_purchase_timestamp", type datetime}, {"purchase_month", type date},
  {"order_delivered_customer_date", type datetime}, {"order_estimated_delivery_date", type datetime},
  {"delivery_delay_days", Int64.Type}, {"payment_value", Currency.Type}, {"payment_transaction_count", Int64.Type},
  {"review_score", type number}, {"review_count", Int64.Type}
 })
in
 Types

// Query: fact_order_item
let
 Source = Csv.Document(File.Contents("data/exports/fact_order_item.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
 Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
 Types = Table.TransformColumnTypes(Headers, {
  {"order_id", type text}, {"order_item_id", Int64.Type}, {"product_id", type text}, {"seller_id", type text},
  {"product_category", type text}, {"seller_state", type text}, {"item_price", Currency.Type}, {"freight_value", Currency.Type}
 })
in
 Types
