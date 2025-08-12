/usr/bin/kafka-topics --create --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1 --topic logs


SELECT 
  endpoint AS "Endpoint",
  method AS "Method", 
  COUNT(*) AS "Requests",
  AVG(size) AS "Average_Size",
  status AS "Status"
FROM parsed_logs
GROUP BY "Endpoint" , "Method", "Status"
ORDER BY "Requests" DESC
LIMIT 10;
