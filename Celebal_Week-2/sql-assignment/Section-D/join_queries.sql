USE shopease_db;

SELECT o.order_id,
	   c.first_name,
       c.last_name,
       o.order_date,
       o.status,
       o.total_amount
FROM orders o 
INNER JOIN customers c
ON o.customer_id = c.customer_id

SELECT io.order_id,
	   p.product_name,
       io.unit_price,
       io.quantity
FROM order_items io
INNER JOIN products p
ON io.product_id = p.product_id

SELECT c.customer_id,
	   c.first_name,
       c.last_name,
       o.order_id,
       o.order_date,
       o.status
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id

SELECT o.order_id,
       c.first_name,
       c.last_name,
       p.product_name,
       oi.quantity,
       o.total_amount
FROM orders o
INNER JOIN customers c
ON o.customer_id = c.customer_id
INNER JOIN order_items oi
ON o.order_id = oi.order_id
INNER JOIN products p
ON oi.product_id = p.product_id;

SELECT p.product_name,
       SUM(oi.quantity) AS total_quantity_sold
FROM products p
INNER JOIN order_items oi
ON p.product_id = oi.product_id
GROUP BY p.product_name
ORDER BY total_quantity_sold DESC;