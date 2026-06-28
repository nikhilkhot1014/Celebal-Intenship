USE shopease_db;

SELECT c.customer_id,
       c.first_name,
       c.last_name,
       COUNT(o.order_id) AS total_orders
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING COUNT(o.order_id) > 1;

SELECT * FROM products
WHERE unit_price = (
    SELECT MAX(unit_price)
    FROM products
);

SELECT order_id,
       status,
       CASE
           WHEN status = 'Delivered' THEN 'Completed'
           WHEN status = 'Shipped' THEN 'On the Way'
           WHEN status = 'Pending' THEN 'Processing'
           WHEN status = 'Cancelled' THEN 'Order Cancelled'
           ELSE 'Unknown'
       END AS status_label
FROM orders;
