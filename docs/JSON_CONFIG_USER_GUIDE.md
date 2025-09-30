# JSON Configuration User Guide: Zero to Hero

*Master XML generation from XSD schemas with simple, powerful JSON configurations*

## Table of Contents
1. [🚀 Getting Started - Your First 5 Minutes](#getting-started)
2. [💡 Core Concepts](#core-concepts) 
3. [🎯 Values and Paths](#values-and-paths)
4. [⭐ Pattern Matching](#pattern-matching)
5. [🔀 Choice Handling](#choice-handling)
6. [📋 Templates for Related Data](#templates)
7. [🏷️ Working with Attributes](#attributes)
8. [🌐 Namespace Handling](#namespaces)
9. [🔧 Advanced Features](#advanced-features)
10. [🏢 Enterprise Examples](#enterprise-examples)
11. [✨ Best Practices](#best-practices)
12. [📚 Quick Reference](#quick-reference)

---

## 🚀 Getting Started

### What This Guide Teaches You

By the end of this guide, you'll be able to:
- Create simple XML configurations in minutes
- Handle complex enterprise schemas with thousands of elements
- Use patterns to configure hundreds of elements at once
- Master choice elements, attributes, and namespaces
- Build maintainable configurations that scale

### Your First Configuration

Let's start with the simplest possible example. Suppose you have this XSD:

**person.xsd:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Person">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Name" type="xs:string"/>
        <xs:element name="Age" type="xs:int"/>
        <xs:element name="Email" type="xs:string" minOccurs="0"/>
      </xs:sequence>
      <xs:attribute name="PersonID" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

Here's your first JSON configuration:

```json
{
  "schema": "person.xsd",
  "values": {
    "Name": "John Smith",
    "Age": "35",
    "Person@PersonID": "PERSON-001"
  }
}
```

**Generated XML:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Person PersonID="PERSON-001">
  <Name>John Smith</Name>
  <Age>35</Age>
  <Email>john.smith@email.com</Email>
</Person>
```

**What happened:**
- ✅ Name and Age got your specified values
- ✅ PersonID attribute was set via `@` syntax
- ✅ Optional Email was auto-generated (system default behavior)
- ✅ Valid XML structure matches XSD requirements

### What Just Happened?

1. **`schema`**: Points to your XSD file
2. **`values`**: Specifies exact values for elements
3. **Magic**: The system automatically generates valid XML structure from your XSD

---

## 💡 Core Concepts

### The Five Building Blocks

Every JSON configuration uses these five concepts:

1. **Values** - Set specific element content
2. **Patterns** - Configure multiple elements at once  
3. **Choices** - Select options from XSD choice elements
4. **Templates** - Manage related data together
5. **Repeats** - Control how many times elements appear

### How the System Works

```
Your XSD → System analyzes structure → Applies your JSON config → Generates XML
```

**Key Principle**: The system generates complete, valid XML automatically. Your JSON configuration just overrides specific parts.

### Configuration Structure

```json
{
  "schema": "your-schema.xsd",
  "mode": "complete",
  
  "values": { /* specific element values */ },
  "patterns": { /* bulk configuration rules */ },
  "choices": { /* choice element selections */ },
  "templates": { /* related data groups */ },
  "repeats": { /* element occurrence counts */ },
  "attributes": { /* attribute values */ },
  "namespaces": { /* namespace handling */ },
  
  "seed": 12345
}
```

---

## 🎯 Values and Paths

### Basic Element Values

Set any element's content:

```json
{
  "values": {
    "BookingID": "TB-001-2024",
    "CustomerName": "Jennifer Martinez",
    "TotalAmount": "1250.00"
  }
}
```

### Nested Elements (Dot Notation)

For nested structures, use dot notation. Consider this XSD:

**travel_booking.xsd:**
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="TravelBooking">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Customer">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="FirstName" type="xs:string"/>
              <xs:element name="LastName" type="xs:string"/>
              <xs:element name="Address">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="Street" type="xs:string"/>
                    <xs:element name="City" type="xs:string"/>
                    <xs:element name="ZipCode" type="xs:string"/>
                  </xs:sequence>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
        <xs:element name="Payment">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Amount" type="xs:decimal"/>
              <xs:element name="Currency" type="xs:string"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

**JSON Configuration:**
```json
{
  "schema": "travel_booking.xsd",
  "values": {
    "Customer.FirstName": "Jennifer",
    "Customer.LastName": "Martinez",
    "Customer.Address.Street": "123 Business Ave",
    "Customer.Address.City": "Seattle", 
    "Customer.Address.ZipCode": "98101",
    "Payment.Amount": "1250.00",
    "Payment.Currency": "USD"
  }
}
```

**Generated XML:**
```xml
<TravelBooking>
  <Customer>
    <FirstName>Jennifer</FirstName>
    <LastName>Martinez</LastName>
    <Address>
      <Street>123 Business Ave</Street>
      <City>Seattle</City>
      <ZipCode>98101</ZipCode>
    </Address>
  </Customer>
  <Payment>
    <Amount>1250.00</Amount>
    <Currency>USD</Currency>
  </Payment>
</TravelBooking>
```

**Dot notation works with any nesting depth - the system automatically builds the XML hierarchy.**

### Absolute Paths (Enterprise Precision)

For complex schemas where element names repeat, use absolute paths. Consider this enterprise scenario:

**enterprise_order.xsd:**
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Order">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Customer">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Name" type="xs:string"/>
              <xs:element name="Address" type="xs:string"/>  <!-- Customer address -->
              <xs:element name="Contact">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="Address" type="xs:string"/>  <!-- Contact address -->
                  </xs:sequence>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
        <xs:element name="Billing">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Address" type="xs:string"/>  <!-- Billing address -->
            </xs:sequence>
          </xs:complexType>
        </xs:element>
        <xs:element name="Shipping">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Address" type="xs:string"/>  <!-- Shipping address -->
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

**Problem with dot notation:**
```json
{
  "values": {
    "Address": "123 Main St"  // Which Address? Ambiguous!
  }
}
```

**Solution with absolute paths:**
```json
{
  "schema": "enterprise_order.xsd",
  "values": {
    "/Order/Customer/Address": "123 Customer Ave",
    "/Order/Customer/Contact/Address": "456 Contact Blvd", 
    "/Order/Billing/Address": "789 Billing St",
    "/Order/Shipping/Address": "321 Shipping Rd"
  }
}
```

**Generated XML:**
```xml
<Order>
  <Customer>
    <Name>John Smith</Name>
    <Address>123 Customer Ave</Address>
    <Contact>
      <Address>456 Contact Blvd</Address>
    </Contact>
  </Customer>
  <Billing>
    <Address>789 Billing St</Address>
  </Billing>
  <Shipping>
    <Address>321 Shipping Rd</Address>
  </Shipping>
</Order>
```

**When to use absolute paths:**
- Element names appear in multiple contexts (like "Address" above)
- You need exact precision with no ambiguity
- Working with enterprise schemas that reuse element names

### Indexed Elements

Control specific instances of repeating elements. Consider this XSD with unbounded passengers:

**multi_passenger.xsd:**
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="GroupBooking">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="BookingID" type="xs:string"/>
        <xs:element name="Passenger" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="FirstName" type="xs:string"/>
              <xs:element name="LastName" type="xs:string"/>
              <xs:element name="Age" type="xs:int"/>
            </xs:sequence>
            <xs:attribute name="PassengerID" type="xs:string" use="required"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

**JSON Configuration:**
```json
{
  "schema": "multi_passenger.xsd",
  "values": {
    "BookingID": "GROUP-001-2024",
    "Passenger[1].FirstName": "John",
    "Passenger[1].LastName": "Smith",
    "Passenger[1].Age": "35",
    "Passenger[1]@PassengerID": "PAX-001",
    "Passenger[2].FirstName": "Jane", 
    "Passenger[2].LastName": "Doe",
    "Passenger[2].Age": "28",
    "Passenger[2]@PassengerID": "PAX-002",
    "Passenger[3].FirstName": "Bob",
    "Passenger[3].LastName": "Johnson", 
    "Passenger[3].Age": "42",
    "Passenger[3]@PassengerID": "PAX-003"
  },
  "repeats": {
    "Passenger": 3
  }
}
```

**Generated XML:**
```xml
<GroupBooking>
  <BookingID>GROUP-001-2024</BookingID>
  <Passenger PassengerID="PAX-001">
    <FirstName>John</FirstName>
    <LastName>Smith</LastName>
    <Age>35</Age>
  </Passenger>
  <Passenger PassengerID="PAX-002">
    <FirstName>Jane</FirstName>
    <LastName>Doe</LastName>
    <Age>28</Age>
  </Passenger>
  <Passenger PassengerID="PAX-003">
    <FirstName>Bob</FirstName>
    <LastName>Johnson</LastName>
    <Age>42</Age>
  </Passenger>
</GroupBooking>
```

### Generated Values

Instead of static values, generate dynamic content:

```json
{
  "values": {
    "BookingID": "generate:uuid",
    "BookingDate": "generate:date:today",
    "ConfirmationCode": "generate:alpha:6"
  }
}
```

**Available generators:**
- `generate:uuid` - Unique identifier
- `generate:date:today` - Current date
- `generate:date:future` - Future date
- `generate:alpha:6` - 6-character alphabetic string
- `generate:number:1000:9999` - Random number in range
- `generate:currency:100:1000` - Currency amount

---

## ⭐ Pattern Matching

### Why Patterns?

Consider this complex e-commerce XSD with many ID fields:

**ecommerce.xsd (snippet):**
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="ECommerceOrder">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="OrderID" type="xs:string"/>
        <xs:element name="CustomerID" type="xs:string"/>
        <xs:element name="Customer">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="AccountID" type="xs:string"/>
              <xs:element name="ProfileID" type="xs:string"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
        <xs:element name="Products">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Product" maxOccurs="unbounded">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="ProductID" type="xs:string"/>
                    <xs:element name="CategoryID" type="xs:string"/>
                    <xs:element name="SupplierID" type="xs:string"/>
                    <xs:element name="Price" type="xs:decimal"/>
                  </xs:sequence>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
        <xs:element name="Payment">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="PaymentID" type="xs:string"/>
              <xs:element name="TransactionID" type="xs:string"/>
              <xs:element name="TotalAmount" type="xs:decimal"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

**Without patterns (tedious):**
```json
{
  "values": {
    "OrderID": "generate:uuid",
    "CustomerID": "generate:uuid",
    "Customer.AccountID": "generate:uuid",
    "Customer.ProfileID": "generate:uuid", 
    "Products.Product.ProductID": "generate:uuid",
    "Products.Product.CategoryID": "generate:uuid",
    "Products.Product.SupplierID": "generate:uuid",
    "Payment.PaymentID": "generate:uuid",
    "Payment.TransactionID": "generate:uuid"
    // Imagine 100 more ID fields...
  }
}
```

**With patterns (efficient):**
```json
{
  "schema": "ecommerce.xsd",
  "patterns": {
    "*ID": "generate:uuid",
    "*Amount": "generate:currency:10:1000"
  },
  "repeats": {
    "Product": 3
  }
}
```

**Generated XML:**
```xml
<ECommerceOrder>
  <OrderID>550e8400-e29b-41d4-a716-446655440001</OrderID>
  <CustomerID>550e8400-e29b-41d4-a716-446655440002</CustomerID>
  <Customer>
    <AccountID>550e8400-e29b-41d4-a716-446655440003</AccountID>
    <ProfileID>550e8400-e29b-41d4-a716-446655440004</ProfileID>
  </Customer>
  <Products>
    <Product>
      <ProductID>550e8400-e29b-41d4-a716-446655440005</ProductID>
      <CategoryID>550e8400-e29b-41d4-a716-446655440006</CategoryID>
      <SupplierID>550e8400-e29b-41d4-a716-446655440007</SupplierID>
      <Price>234.50</Price>
    </Product>
    <Product>
      <ProductID>550e8400-e29b-41d4-a716-446655440008</ProductID>
      <CategoryID>550e8400-e29b-41d4-a716-446655440009</CategoryID>
      <SupplierID>550e8400-e29b-41d4-a716-446655440010</SupplierID>
      <Price>156.75</Price>
    </Product>
    <Product>
      <ProductID>550e8400-e29b-41d4-a716-446655440011</ProductID>
      <CategoryID>550e8400-e29b-41d4-a716-446655440012</CategoryID>
      <SupplierID>550e8400-e29b-41d4-a716-446655440013</SupplierID>
      <Price>89.99</Price>
    </Product>
  </Products>
  <Payment>
    <PaymentID>550e8400-e29b-41d4-a716-446655440014</PaymentID>
    <TransactionID>550e8400-e29b-41d4-a716-446655440015</TransactionID>
    <TotalAmount>481.24</TotalAmount>
  </Payment>
</ECommerceOrder>
```

**Result**: Two simple patterns configured 15+ elements automatically!

### Pattern Syntax

**Wildcard Patterns:**
```json
{
  "patterns": {
    "*ID": "generate:uuid",           // Any element ending in ID
    "*Amount": "generate:currency",   // Any element ending in Amount  
    "*Date": "generate:date:future",  // Any element ending in Date
    "Customer*": "generate:name"      // Any element starting with Customer
  }
}
```

**Context Patterns:**
```json
{
  "patterns": {
    "*/Address": "generate:address:business",    // Any Address element
    "Payment/*": "generate:payment_data",        // Any element inside Payment
    "*/Contact/Email": "generate:email:business" // Email inside any Contact
  }
}
```

### Pattern Examples

**Travel Booking Schema:**
```json
{
  "patterns": {
    "*ID": "generate:uuid:short",
    "*Amount": "generate:currency:100:2000", 
    "*Date": "generate:date:2024-06-01:2024-12-31",
    "*Airport": "generate:airport_code",
    "*/Contact/*": "generate:business_contact"
  }
}
```

**E-commerce Schema:**
```json
{
  "patterns": {
    "*SKU": "generate:sku",
    "*Price": "generate:currency:10:500",
    "Product/*": "generate:product_data",
    "*/Address/*": "generate:shipping_address"
  }
}
```

---

## 🔀 Choice Handling

### Understanding Choices

XSD schemas often have choice elements where you pick one option. Here's a real scenario:

**shipping_options.xsd:**
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Order">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="OrderID" type="xs:string"/>
        <xs:element name="Customer">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="Name" type="xs:string"/>
              <!-- Choice 1: Address Type -->
              <xs:choice>
                <xs:element name="HomeAddress" type="xs:string"/>
                <xs:element name="BusinessAddress" type="xs:string"/>
                <xs:element name="POBoxAddress" type="xs:string"/>
              </xs:choice>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
        <!-- Choice 2: Payment Method -->
        <xs:choice>
          <xs:element name="CreditCard">
            <xs:complexType>
              <xs:sequence>
                <xs:element name="CardNumber" type="xs:string"/>
                <xs:element name="ExpiryDate" type="xs:string"/>
              </xs:sequence>
            </xs:complexType>
          </xs:element>
          <xs:element name="PayPal">
            <xs:complexType>
              <xs:sequence>
                <xs:element name="AccountEmail" type="xs:string"/>
              </xs:sequence>
            </xs:complexType>
          </xs:element>
          <xs:element name="BankTransfer">
            <xs:complexType>
              <xs:sequence>
                <xs:element name="AccountNumber" type="xs:string"/>
                <xs:element name="RoutingNumber" type="xs:string"/>
              </xs:sequence>
            </xs:complexType>
          </xs:element>
        </xs:choice>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

### Simple Choice Selection

**JSON Configuration:**
```json
{
  "schema": "shipping_options.xsd",
  "values": {
    "OrderID": "ORD-001-2024",
    "Customer.Name": "Jennifer Martinez"
  },
  "choices": {
    "Customer": "BusinessAddress",  // Choose business address over home/PO Box
    "Order": "CreditCard"          // Choose credit card over PayPal/bank transfer
  },
  "values": {
    "Customer.BusinessAddress": "100 Corporate Plaza, Suite 200",
    "CreditCard.CardNumber": "4111111111111111",
    "CreditCard.ExpiryDate": "12/2027"
  }
}
```

**Generated XML:**
```xml
<Order>
  <OrderID>ORD-001-2024</OrderID>
  <Customer>
    <Name>Jennifer Martinez</Name>
    <BusinessAddress>100 Corporate Plaza, Suite 200</BusinessAddress>
  </Customer>
  <CreditCard>
    <CardNumber>4111111111111111</CardNumber>
    <ExpiryDate>12/2027</ExpiryDate>
  </CreditCard>
</Order>
```

**Notice**: The system automatically excluded `HomeAddress`, `POBoxAddress`, `PayPal`, and `BankTransfer` based on your choices.

### Path-Specific Choices

For complex schemas, specify the exact choice location:

```json
{
  "choices": {
    "/Customer/AddressChoice": "BusinessAddress",
    "/Delivery/AddressChoice": "HomeAddress"  
  }
}
```

### Conditional Choices

Make choices based on other values:

```json
{
  "choices": {
    "PaymentMethod": {
      "conditions": [
        {"if": "TotalAmount > 1000", "choose": "CreditCard"},
        {"if": "CustomerType == 'Business'", "choose": "InvoiceLater"},
        {"default": "DebitCard"}
      ]
    }
  }
}
```

### Multiple Choice Levels

Handle nested choices:

```json
{
  "choices": {
    "TravelType": "International",
    "InternationalOptions": "BusinessClass",
    "BusinessClassServices": "PriorityBoarding"
  }
}
```

---

## 📋 Templates for Related Data

### Why Templates?

Templates solve the consistency problem with related data. Consider this employee XSD:

**employee_directory.xsd:**
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Company">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Department" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="DepartmentName" type="xs:string"/>
              <xs:element name="Employee" maxOccurs="unbounded">
                <xs:complexType>
                  <xs:sequence>
                    <xs:element name="FirstName" type="xs:string"/>
                    <xs:element name="LastName" type="xs:string"/>
                    <xs:element name="Email" type="xs:string"/>
                    <xs:element name="Phone" type="xs:string"/>
                    <xs:element name="Title" type="xs:string"/>
                    <xs:element name="Salary" type="xs:decimal"/>
                  </xs:sequence>
                  <xs:attribute name="EmployeeID" type="xs:string" use="required"/>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

**Without templates (inconsistent risk):**
```json
{
  "values": {
    "Department[1].Employee[1].FirstName": "Jennifer",
    "Department[1].Employee[1].LastName": "Martinez",
    "Department[1].Employee[1].Email": "d.smith@company.com",  // WRONG EMAIL!
    "Department[1].Employee[1].Phone": "+1-206-555-0100",
    "Department[1].Employee[1].Title": "Senior Developer"
    // Risk: Email doesn't match the name
  }
}
```

**With templates (guaranteed consistency):**
```json
{
  "schema": "employee_directory.xsd",
  "templates": {
    "senior_developers": [
      {
        "FirstName": "Jennifer",
        "LastName": "Martinez", 
        "Email": "j.martinez@techcorp.com",
        "Phone": "+1-206-555-0100",
        "Title": "Senior Full-Stack Developer",
        "Salary": "125000",
        "EmployeeID": "EMP-001"
      },
      {
        "FirstName": "David",
        "LastName": "Wilson",
        "Email": "d.wilson@techcorp.com", 
        "Phone": "+1-206-555-0101",
        "Title": "Senior Backend Developer",
        "Salary": "128000",
        "EmployeeID": "EMP-002"
      }
    ]
  },
  "values": {
    "Department[1].DepartmentName": "Engineering",
    "Department[1].Employee[1]": "@senior_developers[1]",
    "Department[1].Employee[2]": "@senior_developers[2]"
  },
  "repeats": {
    "Department": 1,
    "Employee": 2
  }
}
```

**Generated XML:**
```xml
<Company>
  <Department>
    <DepartmentName>Engineering</DepartmentName>
    <Employee EmployeeID="EMP-001">
      <FirstName>Jennifer</FirstName>
      <LastName>Martinez</LastName>
      <Email>j.martinez@techcorp.com</Email>
      <Phone>+1-206-555-0100</Phone>
      <Title>Senior Full-Stack Developer</Title>
      <Salary>125000</Salary>
    </Employee>
    <Employee EmployeeID="EMP-002">
      <FirstName>David</FirstName>
      <LastName>Wilson</LastName>
      <Email>d.wilson@techcorp.com</Email>
      <Phone>+1-206-555-0101</Phone>
      <Title>Senior Backend Developer</Title>
      <Salary>128000</Salary>
    </Employee>
  </Department>
</Company>
```

**Benefit**: Names, emails, titles, and IDs are guaranteed to be consistent for each employee.

### Template Cycling

Automatically cycle through template data:

```json
{
  "templates": {
    "passengers": {
      "cycle": "sequential",
      "data": [
        {"FirstName": "John", "LastName": "Smith"},
        {"FirstName": "Jane", "LastName": "Doe"},
        {"FirstName": "Bob", "LastName": "Johnson"}
      ]
    }
  },
  "values": {
    "Passenger.FirstName": "@passengers.FirstName",
    "Passenger.LastName": "@passengers.LastName"
  },
  "repeats": {
    "Passenger": 5  // Will cycle: John, Jane, Bob, John, Jane
  }
}
```

### Template with Computed Fields

Templates can include calculations:

```json
{
  "templates": {
    "flight_segments": {
      "data": [
        {
          "DepartureAirport": "SEA",
          "ArrivalAirport": "LAX",
          "DepartureTime": "2024-10-15T08:00:00"
        }
      ],
      "computed": {
        "ArrivalTime": "DepartureTime + 2h30m",
        "FlightDuration": "calculate:flight_time"
      }
    }
  }
}
```

---

## 🏷️ Working with Attributes

### Basic Attribute Setting

Set element attributes using `@` syntax:

```json
{
  "values": {
    "Passenger@PassengerID": "PAX-001",
    "Passenger@Type": "Adult",
    "FlightSegment@SegmentID": "SEG-001"
  }
}
```

### Attribute Patterns

Apply patterns to attributes:

```json
{
  "patterns": {
    "*@*ID": "generate:uuid:short",     // Any attribute ending in ID
    "*@Currency": "USD",                // Any Currency attribute
    "*@Status": "Active"                // Any Status attribute
  }
}
```

### Path-Specific Attributes

For precision with complex schemas:

```json
{
  "values": {
    "/Order/Customer@CustomerID": "CUST-001",
    "/Order/Payment@PaymentID": "PAY-001",
    "/Order/Delivery@TrackingID": "TRK-001"
  }
}
```

### Dedicated Attribute Section

For attribute-heavy schemas:

```json
{
  "attributes": {
    "//*[@PassengerID]": "generate:passenger_id",
    "//FlightSegment/@SegmentKey": "generate:segment_key", 
    "//Payment/@ProcessingMethod": "Immediate",
    "//*[@Currency]": "USD"
  }
}
```

---

## 🌐 Namespace Handling

### Understanding Namespaces

Enterprise XSD schemas often use multiple namespaces for different domains. Here's a realistic example:

**multi_namespace_order.xsd:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema 
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:travel="http://schemas.example.com/travel/v2"
  xmlns:payment="http://schemas.example.com/payment/v1"
  xmlns:common="http://schemas.example.com/common/v1"
  targetNamespace="http://schemas.example.com/travel/v2"
  elementFormDefault="qualified">
  
  <xs:import namespace="http://schemas.example.com/payment/v1" 
             schemaLocation="payment_types.xsd"/>
  <xs:import namespace="http://schemas.example.com/common/v1" 
             schemaLocation="common_types.xsd"/>
  
  <xs:element name="TravelOrder">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="OrderID" type="xs:string"/>
        <xs:element name="Customer" type="common:PersonType"/>
        <xs:element name="Booking" type="travel:BookingType"/>
        <xs:element name="Payment" type="payment:PaymentType"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  
  <xs:complexType name="BookingType">
    <xs:sequence>
      <xs:element name="FlightNumber" type="xs:string"/>
      <xs:element name="DepartureDate" type="xs:date"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
```

**payment_types.xsd:**
```xml
<xs:schema 
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://schemas.example.com/payment/v1">
  
  <xs:complexType name="PaymentType">
    <xs:sequence>
      <xs:element name="Amount" type="xs:decimal"/>
      <xs:element name="Currency" type="xs:string"/>
      <xs:element name="Method" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
```

**common_types.xsd:**
```xml
<xs:schema 
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  targetNamespace="http://schemas.example.com/common/v1">
  
  <xs:complexType name="PersonType">
    <xs:sequence>
      <xs:element name="FirstName" type="xs:string"/>
      <xs:element name="LastName" type="xs:string"/>
      <xs:element name="Email" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
```

### Namespace Configuration

**JSON Configuration:**
```json
{
  "schema": "multi_namespace_order.xsd",
  "namespaces": {
    "prefixes": {
      "travel": "http://schemas.example.com/travel/v2",
      "payment": "http://schemas.example.com/payment/v1", 
      "common": "http://schemas.example.com/common/v1"
    },
    "default": "http://schemas.example.com/travel/v2"
  },
  "values": {
    "OrderID": "TRV-001-2024",
    "{common}Customer.FirstName": "Jennifer",
    "{common}Customer.LastName": "Martinez",
    "{common}Customer.Email": "j.martinez@company.com",
    "{travel}Booking.FlightNumber": "AA1234",
    "{travel}Booking.DepartureDate": "2024-12-15",
    "{payment}Payment.Amount": "875.50",
    "{payment}Payment.Currency": "USD",
    "{payment}Payment.Method": "CreditCard"
  }
}
```

**Generated XML:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<travel:TravelOrder 
  xmlns:travel="http://schemas.example.com/travel/v2"
  xmlns:payment="http://schemas.example.com/payment/v1"
  xmlns:common="http://schemas.example.com/common/v1">
  
  <travel:OrderID>TRV-001-2024</travel:OrderID>
  
  <common:Customer>
    <common:FirstName>Jennifer</common:FirstName>
    <common:LastName>Martinez</common:LastName>
    <common:Email>j.martinez@company.com</common:Email>
  </common:Customer>
  
  <travel:Booking>
    <travel:FlightNumber>AA1234</travel:FlightNumber>
    <travel:DepartureDate>2024-12-15</travel:DepartureDate>
  </travel:Booking>
  
  <payment:Payment>
    <payment:Amount>875.50</payment:Amount>
    <payment:Currency>USD</payment:Currency>
    <payment:Method>CreditCard</payment:Method>
  </payment:Payment>
  
</travel:TravelOrder>
```

**Notice**: Each element gets the correct namespace prefix based on its schema definition.

### Namespace-Qualified Elements

Reference elements with namespace prefixes:

```json
{
  "values": {
    "{travel}BookingID": "TB-001-2024",
    "{payment}Amount": "1250.00",
    "{common}Address": "123 Main St"
  }
}
```

### Namespace Patterns

Apply patterns by namespace:

```json
{
  "patterns": {
    "{payment}*Amount": "generate:currency",
    "{travel}*ID": "generate:uuid",
    "{common}*Address": "generate:address"
  }
}
```

---

## 🔧 Advanced Features

### Conditional Configuration

Apply configuration based on conditions:

```json
{
  "conditional": {
    "rules": [
      {
        "if": {"TripType": "International"},
        "then": {
          "values": {"DocumentRequired": "true"},
          "patterns": {"*Visa*": "generate:visa_data"}
        }
      },
      {
        "if": {"PassengerCount": "> 5"}, 
        "then": {
          "choices": {"BookingType": "Group"},
          "patterns": {"*Discount*": "generate:group_discount"}
        }
      }
    ]
  }
}
```

### Configuration Inheritance

Build configurations from base templates:

```json
{
  "extends": "base_travel_config.json",
  "values": {
    "BookingType": "Business",  // Override base value
    "Priority": "High"          // Add new value
  }
}
```

### Multi-Schema Support

Handle schemas that reference other schemas:

```json
{
  "schemas": {
    "primary": "OrderCreateRQ.xsd",
    "common": "edist_commontypes.xsd",
    "aidm": "aidm_commontypes.xsd"
  },
  "schema_mapping": {
    "OrderCreate*": "primary",
    "Common*": "common",
    "AIDM*": "aidm"
  }
}
```

### Validation Rules

Add business rule validation:

```json
{
  "validation": {
    "rules": [
      {
        "field": "DepartureTime",
        "condition": "before",
        "target": "ArrivalTime",
        "message": "Departure must be before arrival"
      },
      {
        "field": "PassengerAge", 
        "condition": "range",
        "min": 0,
        "max": 120,
        "message": "Invalid passenger age"
      }
    ]
  }
}
```

---

## 🏢 Enterprise Examples

### Example 1: IATA OrderCreate (Airline Industry)

```json
{
  "schema": "OrderCreateRQ.xsd",
  "mode": "complete",
  
  "values": {
    "/OrderCreateRQ/@Version": "5.000",
    "/OrderCreateRQ/Document/@ReferenceVersion": "1.0",
    "/OrderCreateRQ/Party/Sender/@Name": "TravelAgency",
    "/OrderCreateRQ/Query/Order/OrderItems/ShoppingResponse/@ResponseID": "RESP-001"
  },
  
  "patterns": {
    "*ID": "generate:uuid:short",
    "*Amount": "generate:currency:100:5000",
    "*Date": "generate:date:2024-06-01:2024-12-31",
    "*/Contact/*": "generate:business_contact"
  },
  
  "templates": {
    "business_passengers": [
      {
        "Individual": {
          "GivenName": "Jennifer", 
          "Surname": "Martinez",
          "TitleName": "Ms."
        },
        "ContactInfoRefID": "CONTACT-001"
      }
    ]
  },
  
  "choices": {
    "/OrderCreateRQ/Query/Order/OrderItems": "ShoppingResponse"
  },
  
  "repeats": {
    "Passenger": 1,
    "OrderItem": 1
  },
  
  "namespaces": {
    "prefixes": {
      "iata": "http://www.iata.org/IATA/2015/00/2019.2"
    }
  }
}
```

### Example 2: AMA Connectivity Layer (Amadeus)

```json
{
  "schema": "AMA_ConnectivityLayerRQ.xsd",
  "mode": "minimal",
  
  "values": {
    "/AMA_ConnectivityLayerRQ/@Version": "1.0",
    "/AMA_ConnectivityLayerRQ/Request/RequestID": "REQ-AMA-001-2024"
  },
  
  "patterns": {
    "{ama}*ID": "generate:amadeus_id",
    "{ota}*Code": "generate:iata_code", 
    "*Amount": "generate:currency:50:2000"
  },
  
  "namespaces": {
    "prefixes": {
      "ama": "http://xml.amadeus.com/2010/06/Types_v2",
      "ota": "http://www.opentravel.org/OTA/2003/05/OTA2011A",
      "etr": "http://xml.amadeus.com/2010/06/ETR_Types_v2"
    }
  }
}
```

### Example 3: E-commerce Order (Complex Retail)

```json
{
  "schema": "ecommerce_order.xsd",
  "mode": "complete",
  
  "values": {
    "OrderID": "ORD-2024-001",
    "Customer.CustomerID": "CUST-VIP-001",
    "Customer.Tier": "Platinum"
  },
  
  "patterns": {
    "*SKU": "generate:sku:electronics",
    "*Price": "generate:currency:25:500",
    "Product/*": "generate:product_data:electronics",
    "*/Shipping/*": "generate:shipping_data:express"
  },
  
  "templates": {
    "vip_customers": [
      {
        "FirstName": "Sarah",
        "LastName": "Chen", 
        "Email": "s.chen@techcorp.com",
        "ShippingPreference": "Express",
        "BillingAddress": {
          "Street": "100 Tech Plaza",
          "City": "San Francisco",
          "State": "CA",
          "Zip": "94105"
        }
      }
    ]
  },
  
  "choices": {
    "PaymentMethod": "CorporateCard",
    "ShippingMethod": "NextDay"
  },
  
  "repeats": {
    "OrderItem": 3,
    "ShippingAddress": 1
  }
}
```

---

## ✨ Best Practices

### 1. Start Simple, Add Complexity

**Begin with basic values:**
```json
{
  "schema": "order.xsd",
  "values": {
    "OrderID": "ORD-001",
    "CustomerName": "John Smith"
  }
}
```

**Add patterns as you grow:**
```json
{
  "schema": "order.xsd", 
  "values": {
    "CustomerName": "John Smith"
  },
  "patterns": {
    "*ID": "generate:uuid",
    "*Amount": "generate:currency"
  }
}
```

### 2. Use Absolute Paths for Precision

**When element names repeat, be specific:**
```json
{
  "values": {
    "/Order/Customer/Address": "Billing address",
    "/Order/Shipping/Address": "Shipping address"
  }
}
```

### 3. Patterns for Efficiency

**Instead of many individual values:**
```json
{
  "values": {
    "ProductID": "generate:uuid",
    "OrderID": "generate:uuid", 
    "CustomerID": "generate:uuid",
    "ShipmentID": "generate:uuid"
  }
}
```

**Use a pattern:**
```json
{
  "patterns": {
    "*ID": "generate:uuid"
  }
}
```

### 4. Templates for Consistency

**For related data that should stay together:**
```json
{
  "templates": {
    "customers": [
      {
        "FirstName": "John",
        "LastName": "Smith",
        "Email": "j.smith@email.com",
        "Phone": "+1-555-0100"
      }
    ]
  }
}
```

### 5. Organization Tips

**Structure your configuration logically:**
```json
{
  "schema": "complex_schema.xsd",
  
  // Basic settings first
  "mode": "complete",
  "seed": 12345,
  
  // Core values 
  "values": { /* ... */ },
  
  // Bulk patterns
  "patterns": { /* ... */ },
  
  // Choice decisions
  "choices": { /* ... */ },
  
  // Related data
  "templates": { /* ... */ },
  
  // Repetition controls  
  "repeats": { /* ... */ },
  
  // Advanced features
  "namespaces": { /* ... */ },
  "attributes": { /* ... */ }
}
```

### 6. Naming Conventions

**Use clear, descriptive names:**
```json
{
  "templates": {
    "business_travelers": [/* ... */],    // Not "template1"
    "international_flights": [/* ... */], // Not "data" 
    "vip_customers": [/* ... */]          // Not "users"
  }
}
```

### 7. Testing Strategy

**Start with minimal config:**
```json
{
  "schema": "test.xsd",
  "mode": "minimal",
  "values": {
    "RequiredField1": "test",
    "RequiredField2": "test"
  }
}
```

**Gradually add complexity:**
```json
{
  "schema": "test.xsd", 
  "mode": "complete",
  "values": { /* ... */ },
  "patterns": { /* ... */ },
  "templates": { /* ... */ }
}
```

---

## 📚 Quick Reference

### Basic Structure
```json
{
  "schema": "file.xsd",
  "mode": "complete|minimal",
  "seed": 12345
}
```

### Values
```json
{
  "values": {
    "ElementName": "value",
    "Parent.Child": "value",
    "Element[2]": "value",
    "/absolute/path": "value",
    "Element@attribute": "value",
    "{namespace}Element": "value"
  }
}
```

### Patterns  
```json
{
  "patterns": {
    "*suffix": "value",
    "prefix*": "value", 
    "*/path": "value",
    "*@attribute": "value"
  }
}
```

### Generators
```json
{
  "values": {
    "field": "generate:uuid",
    "field": "generate:date:today",
    "field": "generate:alpha:6",
    "field": "generate:number:100:999",
    "field": "generate:currency:10:100"
  }
}
```

### Templates
```json
{
  "templates": {
    "template_name": [
      {"field1": "value1", "field2": "value2"}
    ]
  },
  "values": {
    "Element": "@template_name[1]"
  }
}
```

### Choices
```json
{
  "choices": {
    "ChoiceElement": "SelectedOption",
    "/path/ChoiceElement": "Option"
  }
}
```

### Repeats
```json
{
  "repeats": {
    "ElementName": 3
  }
}
```

### Namespaces
```json
{
  "namespaces": {
    "prefixes": {
      "ns": "http://example.com/namespace"
    }
  }
}
```

### Mode Options
- **`complete`**: Generate all possible elements
- **`minimal`**: Generate only required elements

---

**🎉 Congratulations!** You've mastered JSON configuration for XML generation. You can now handle everything from simple schemas to complex enterprise systems with thousands of elements.

**Pro Tip**: Start simple and gradually add complexity as your needs grow. The system is designed to scale with you from basic configs to enterprise-level complexity.