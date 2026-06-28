USE shopease_db;

SELECT * FROM orders where status = 'Delivered'

SELECT * FROM products WHERE unit_price > 2000 and category = 'Electronics'

SELECT * FROM customers WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31' 
AND state = 'Maharashtra';

SELECT * FROM orders WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25' 
AND status <> 'Cancelled' ;

SELECT * FROM orders WHERE order_date = '2024-08-15';

SELECT * FROM customers WHERE YEAR(join_date) = 2024;