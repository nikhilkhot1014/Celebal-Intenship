USE shopease_db

SELECT COUNT(*) AS total_order FROM orders

SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'Delivered';

SELECT category, AVG(unit_price) AS average_price FROM products GROUP BY category;

SELECT status, COUNT(*) AS total_orders, 
	SUM(total_amount) AS total_revenue 
FROM orders
GROUP BY status 
ORDER BY total_revenue DESC;

SELECT category,
       MAX(unit_price) AS most_expensive,
       MIN(unit_price) AS cheapest
FROM products
GROUP BY category;

SELECT category,
       AVG(unit_price) AS average_price
FROM products
GROUP BY category
HAVING AVG(unit_price) > 2000;
