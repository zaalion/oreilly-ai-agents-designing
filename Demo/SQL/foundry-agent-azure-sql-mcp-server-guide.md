# Query Azure SQL from a Microsoft Foundry Agent Using MCP

## Goal

This guide shows how to let a **Microsoft Foundry agent** query data from an **Azure SQL Database** by using a **SQL MCP Server**.

The recommended architecture is:

```text
Microsoft Foundry Agent
        ↓
Custom MCP Tool
        ↓
SQL MCP Server / Data API Builder
        ↓
Azure SQL Database
```

---

## Important Clarification: Azure MCP Server vs SQL MCP Server

There are two MCP-related options that are easy to confuse.

| MCP option | Best for | Azure SQL behavior |
|---|---|---|
| **Azure MCP Server** | Managing Azure resources | List/manage Azure SQL servers, databases, firewall rules, elastic pools, and other Azure resources |
| **SQL MCP Server** | Querying business data in SQL | Exposes selected tables, views, and stored procedures as MCP tools |

For this scenario, where a Foundry agent needs to answer questions from data inside Azure SQL, use:

```text
Foundry Agent → SQL MCP Server → Azure SQL Database
```

Do **not** use Azure MCP Server as the main path for querying business data from tables.

Azure MCP Server is useful for management tasks such as:

```text
List my Azure SQL databases
Show SQL firewall rules
Check SQL server metadata
Review Azure resource configuration
```

SQL MCP Server is useful for data questions such as:

```text
Show products with low inventory
Find customers from Canada
List recent orders
Summarize sales by region
Run a stored procedure
```

---

## Can Foundry Create the MCP Server?

No. Microsoft Foundry can **connect to** an MCP server, but it does not create or host the MCP server for you.

The MCP server must run somewhere else, such as:

| Hosting option | Good for |
|---|---|
| **Azure Container Apps** | Recommended practical option |
| Azure App Service | Possible |
| Azure Functions | Possible, but less natural for a long-running MCP server |
| Local machine | Testing only |
| AKS | Larger production environments |

In Foundry, you register the MCP server as a tool by providing its URL.

Example:

```text
https://my-sql-mcp-server.azurecontainerapps.io/mcp
```

---

## Step 1: Prepare Azure SQL Database

Use an existing Azure SQL Database or create a new one.

Create a dedicated SQL user for the MCP server. For a demo, you can use a read-only user.

```sql
CREATE USER mcp_reader WITH PASSWORD = 'Use-A-Strong-Password-Here!';
GO

ALTER ROLE db_datareader ADD MEMBER mcp_reader;
GO
```

For production, avoid broad `db_datareader` access. Instead, create a custom role and grant access only to the required tables, views, or stored procedures.

Example demo table:

```sql
CREATE TABLE dbo.Products
(
    ProductID INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    ProductName NVARCHAR(100) NOT NULL,
    Category NVARCHAR(50) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    UnitsInStock INT NOT NULL
);
```

Example seed data:

```sql
INSERT INTO dbo.Products (ProductName, Category, UnitPrice, UnitsInStock)
VALUES
('Laptop', 'Electronics', 1200.00, 25),
('Keyboard', 'Electronics', 75.00, 120),
('Office Chair', 'Furniture', 250.00, 40),
('Desk', 'Furniture', 500.00, 15),
('Monitor', 'Electronics', 300.00, 60);
```

---

## Step 2: Install Data API Builder

The SQL MCP Server capability is provided through **Data API Builder**.

Create a folder for the MCP server project:

```powershell
mkdir sql-mcp-demo
cd sql-mcp-demo
```

Install Data API Builder as a local .NET tool:

```powershell
dotnet new tool-manifest
dotnet tool install microsoft.dataapibuilder
```

Check the version:

```powershell
dotnet tool run dab --version
```

Or, if `dab` is available directly:

```powershell
dab --version
```

---

## Step 3: Create the DAB Configuration

Set your Azure SQL connection string:

```powershell
$CONNECTION_STRING = "Server=tcp:<your-sql-server>.database.windows.net,1433;Database=<your-database>;User ID=mcp_reader;Password=<password>;Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;"
```

Initialize the DAB configuration:

```powershell
dab init `
  --database-type mssql `
  --connection-string "@env('MSSQL_CONNECTION_STRING')" `
  --host-mode Production `
  --config dab-config.json
```

This creates a file named:

```text
dab-config.json
```

The configuration uses the environment variable `MSSQL_CONNECTION_STRING` instead of storing the connection string directly in the config file.

---

## Step 4: Expose a SQL Table as an MCP Entity

Add the `Products` table as an entity:

```powershell
dab add Products `
  --source dbo.Products `
  --permissions "anonymous:read" `
  --description "Product catalog with product names, categories, prices, and inventory levels."
```

For a simple demo, `anonymous:read` is acceptable.

For production, use authentication and least-privilege permissions.

---

## Step 5: Add Field Descriptions

Descriptions help the agent understand what each field means.

```powershell
dab update Products `
  --fields.name ProductID `
  --fields.description "Unique product identifier" `
  --fields.primary-key true

dab update Products `
  --fields.name ProductName `
  --fields.description "Name of the product"

dab update Products `
  --fields.name Category `
  --fields.description "Product category"

dab update Products `
  --fields.name UnitPrice `
  --fields.description "Retail price per unit"

dab update Products `
  --fields.name UnitsInStock `
  --fields.description "Current inventory count"
```

---

## Step 6: Test the MCP Server Locally

Set the environment variable:

```powershell
$env:MSSQL_CONNECTION_STRING = $CONNECTION_STRING
```

Start Data API Builder:

```powershell
dab start
```

Test the health endpoint:

```powershell
curl http://localhost:5000/health
```

The local MCP endpoint should be:

```text
http://localhost:5000/mcp
```

You can test the MCP endpoint with MCP Inspector:

```powershell
npx -y @modelcontextprotocol/inspector http://localhost:5000/mcp
```

---

## Step 7: Deploy the SQL MCP Server to Azure Container Apps

Create a `Dockerfile` in the same folder as `dab-config.json`.

```dockerfile
FROM mcr.microsoft.com/azure-databases/data-api-builder:2.0.0-rc
COPY dab-config.json /App/dab-config.json
```

Set deployment variables:

```powershell
$RESOURCE_GROUP = "rg-sql-mcp"
$LOCATION = "eastus"
$ACR_NAME = "acrsqlmcpdemo12345"
$CONTAINERAPP_ENV = "sql-mcp-env"
$CONTAINERAPP_NAME = "sql-mcp-server"
```

Create the resource group:

```powershell
az group create `
  --name $RESOURCE_GROUP `
  --location $LOCATION
```

Create Azure Container Registry:

```powershell
az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --admin-enabled true
```

Build and push the image:

```powershell
az acr build `
  --registry $ACR_NAME `
  --image sql-mcp-server:1 `
  .
```

Create the Container Apps environment:

```powershell
az containerapp env create `
  --name $CONTAINERAPP_ENV `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION
```

Get ACR details:

```powershell
$ACR_LOGIN_SERVER = az acr show `
  --name $ACR_NAME `
  --query loginServer `
  --output tsv

$ACR_USERNAME = az acr credential show `
  --name $ACR_NAME `
  --query username `
  --output tsv

$ACR_PASSWORD = az acr credential show `
  --name $ACR_NAME `
  --query "passwords[0].value" `
  --output tsv
```

Deploy the container app:

```powershell
az containerapp create `
  --name $CONTAINERAPP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINERAPP_ENV `
  --image "$ACR_LOGIN_SERVER/sql-mcp-server:1" `
  --registry-server $ACR_LOGIN_SERVER `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --target-port 5000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --secrets "mssql-connection-string=$CONNECTION_STRING" `
  --env-vars "MSSQL_CONNECTION_STRING=secretref:mssql-connection-string" `
  --cpu 0.5 `
  --memory 1.0Gi
```

Get the MCP server URL:

```powershell
$MCP_HOST = az containerapp show `
  --name $CONTAINERAPP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "properties.configuration.ingress.fqdn" `
  --output tsv

Write-Host "https://$MCP_HOST/mcp"
```

Test the health endpoint:

```powershell
curl "https://$MCP_HOST/health"
```

Your hosted MCP endpoint should look like this:

```text
https://<your-container-app-fqdn>/mcp
```

---

## Step 8: Allow the MCP Server to Reach Azure SQL

For a quick demo, allow Azure services to connect to Azure SQL:

```powershell
az sql server firewall-rule create `
  --resource-group <sql-resource-group> `
  --server <sql-server-name> `
  --name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0
```

For production, prefer a more secure setup:

- Private endpoint for Azure SQL
- VNet integration for Azure Container Apps
- Managed identity where supported
- Key Vault for secrets
- No public unauthenticated MCP endpoint
- Least-privilege SQL permissions

---

## Step 9: Add the MCP Tool to the Foundry Agent

In Microsoft Foundry:

1. Go to `https://ai.azure.com`.
2. Open your Foundry project.
3. Go to the agent playground.
4. Open or create your agent.
5. Go to **Tools**.
6. Select **Add**.
7. Choose **Add a new tool**.
8. Select the **Custom** tab.
9. Choose **Model Context Protocol (MCP)**.
10. Create the tool.
11. Give it a name, for example:

```text
products-sql-mcp
```

12. Enter the remote MCP endpoint:

```text
https://<your-container-app-fqdn>/mcp
```

13. For a simple demo, choose:

```text
Unauthenticated
```

14. Select **Connect**.

---

## Step 10: Add Agent Instructions

Add instructions similar to this:

```text
You can answer questions about product catalog data using the SQL MCP tool.

Use the Products entity when the user asks about product names, categories, prices, or inventory levels.

Do not invent database results. If the data is not available through the tool, say that the data is not available.
```

A more business-style version:

```text
You are a product inventory assistant. Use the SQL MCP tool to retrieve product information from the Azure SQL database. Always use the tool for product, price, category, and inventory questions. Do not guess database values.
```

---

## Step 11: Test the Agent

In the Foundry chat playground, try:

```text
Show me all products in the database.
```

```text
Which products are in the Electronics category?
```

```text
Which products have fewer than 50 units in stock?
```

```text
What is the most expensive product?
```

The expected flow is:

```text
User prompt
   ↓
Foundry agent decides to use MCP tool
   ↓
MCP tool calls SQL MCP Server
   ↓
SQL MCP Server queries Azure SQL
   ↓
Result is returned to the agent
   ↓
Agent answers the user
```

---

## Production Recommendations

| Area | Recommendation |
|---|---|
| SQL access | Use a dedicated least-privilege identity |
| Data exposure | Expose views or stored procedures instead of raw tables |
| Permissions | Start with read-only |
| MCP endpoint | Protect with authentication |
| Secrets | Use Key Vault or Container Apps secrets |
| Network | Prefer private endpoint and VNet integration |
| Monitoring | Enable Application Insights and Log Analytics |
| Agent instructions | Clearly tell the agent when to use the SQL MCP tool |
| Data safety | Do not expose sensitive tables directly |
| Write operations | Avoid write access unless absolutely required |

---

## Simple Course-Friendly Explanation

You can explain it to learners this way:

> Microsoft Foundry provides the agent runtime and allows the agent to connect to MCP tools. The MCP server itself is a separate application that you host, for example in Azure Container Apps. In this scenario, the SQL MCP Server acts as a secure bridge between the Foundry agent and Azure SQL Database.

Another short version:

> Foundry does not host the MCP server. Foundry connects to it. The MCP server is responsible for safely exposing selected SQL data to the agent.

---

## Final Recommended Demo Architecture

```text
Azure SQL Database
        ↓
SQL MCP Server / Data API Builder
        ↓
Azure Container Apps
        ↓
Microsoft Foundry Agent MCP Tool
        ↓
User asks database questions in chat
```

## Reference

[Quickstart: Use SQL MCP Server with Azure Container Apps]( https://learn.microsoft.com/en-us/azure/data-api-builder/mcp/quickstart-azure-container-apps?tabs=windows)

