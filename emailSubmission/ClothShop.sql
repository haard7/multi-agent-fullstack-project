CREATE TABLE Products (
    ProductID INT PRIMARY KEY,
    ProductName TEXT,
    ProductBrand TEXT,
    ProductSize VARCHAR(10),
    Gender VARCHAR(10),
    Price INT,
    NumImages INT,
    Description TEXT,
    PrimaryColor VARCHAR(20),
    ImageUrl TEXT
);

INSERT INTO
    Products (
        ProductID,
        ProductName,
        ProductBrand,
        ProductSize,
        Gender,
        Price,
        NumImages,
        Description,
        PrimaryColor,
        ImageUrl
    )
VALUES
    (
        10017413,
        'Printed Medium Trolley Bag',
        'DKNY',
        'M',
        'Unisex',
        40,
        7,
        'Black and grey printed medium trolley bag, secured with a TSA lock. One handle on the top and one on the side, has a trolley with a retractable handle on the top and four corner mounted inline skate wheels. One main zip compartment, zip lining, two compression straps with click clasps, one zip compartment on the flap with three zip pockets. Warranty: 5 years. Warranty provided by Brand Owner / Manufacturer',
        'Black',
        'https://i.imgur.com/VTklGP8.png'
    ),
    (
        10016283,
        'Women Beige & Grey Kurta Set',
        'EthnoVogue',
        'L',
        'Women',
        30,
        7,
        'Beige & Grey made to measure kurta with churidar and dupatta. Beige made to measure calf length kurta, has a V-neck, three-quarter sleeves, lightly padded on bust, flared hem, concealed zip closure. Grey solid made to measure churidar, drawstring closure. Grey net sequined dupatta, has printed taping. What is Made to Measure? Customised Kurta Set according to your Bust and Length. So please refer to the Size Chart to pick your perfect size. How to measure bust? Measure under your arms and around your chest to find your bust size in inches. How to measure Kurta length? Measure from shoulder till barefoot to find kurta length',
        'Beige',
        'https://i.imgur.com/VDzDTh7.jpeg'
    ),
    (
        10009781,
        'SPYKAR Women Pink Cropped Jeans',
        'SPYKAR',
        'S',
        'Women',
        30,
        7,
        'Pink coloured wash 5-pocket high-rise cropped jeans, clean look, no fade, has a button and zip closure, and waistband with belt loops',
        'Pink',
        'https://i.imgur.com/7nQ7ofi.png'
    ),
    (
        10015921,
        'Raymond Men Blue Bandhgala Suit',
        'Raymond',
        'M',
        'Men',
        40,
        5,
        'Blue self-design bandhgala suit. Blue self-design bandhgala blazer, has a mandarin collar, single breasted with full button placket, long sleeves, three pockets, an attached lining and a double-vented back hem. Blue self-design mid-rise trousers, has a zip fly with a button and a hook-and-bar closure, four pockets, a waistband with belt loops',
        'Blue',
        'https://i.imgur.com/qTNSCJm.png'
    ),
    (
        10017833,
        'Parx Men Brown Casual Shirt',
        'Parx',
        'L',
        'Men',
        35,
        5,
        'Brown and off-white printed casual shirt, has a spread collar, long sleeves, button placket, curved hem, one patch pocket',
        'Brown',
        'https://i.imgur.com/rJgzr4F.jpeg'
    ),
    (
        10014361,
        'Men Brown Solid Slim Fit Regular Shorts',
        'SHOWOFF',
        'L',
        'Men',
        25,
        5,
        'Brown solid low-rise regular shorts, has four pockets, a button closure',
        'Brown',
        'https://i.imgur.com/XqIy8vE.png'
    ),
    (
        10017900,
        'Men Black Solid Slim Fit Regular Shorts',
        'SHOWOFF',
        'XL',
        'Men',
        30,
        5,
        'Black solid low-rise regular shorts, has four pockets, a button closure',
        'Black',
        'https://i.imgur.com/Uf3MmBg.png'
    ),
    (
        10017901,
        'Pink Men Solid Slim Fit Regular Shorts',
        'SHOWOFF',
        'S',
        'Men',
        30,
        5,
        'Pink regular shorts, has four pockets, a button closure',
        'Pink',
        'https://i.imgur.com/syvRx9w.png'
    );

SELECT
    *
FROM
    Products;

CREATE TABLE Customers (
    CustomerID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    FirstName TEXT,
    LastName TEXT,
    Email TEXT,
    PhoneNumber TEXT,
    ShippingAddress TEXT,
    CreditCardNumber TEXT
);

INSERT INTO
    Customers (
        FirstName,
        LastName,
        Email,
        PhoneNumber,
        ShippingAddress,
        CreditCardNumber
    )
VALUES
    (
        'John',
        'Doe',
        'john.doe@example.com',
        '555-1234',
        '123 Elm Street',
        '1234567812345678'
    ),
    (
        'Jane',
        'Smith',
        'jane.smith@example.com',
        '555-5678',
        '456 Oak Avenue',
        '8765432187654321'
    );

SELECT
    *
FROM
    Customers;

CREATE TABLE Orders (
    OrderID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CustomerID INT,
    ProductID INT,
    OrderDate DATE,
    Quantity INT,
    TotalPrice INT,
    OrderStatus TEXT,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

SELECT
    *
FROM
    Orders;

-- updated with new Table: product_returns

CREATE TABLE Product_defect (
    orderid INT PRIMARY KEY,
    product_img VARCHAR(255) NOT NULL
);

INSERT INTO Product_defect (orderid, defect_product_img)
VALUES 
    (11, 'https://i.imgur.com/mY5e7mx.png'),
    (12, 'https://i.imgur.com/syvRx9w.png'),
    (13, 'https://i.imgur.com/9GgyJE5.png');

	
CREATE TABLE Package_damaged (
    orderid INT PRIMARY KEY,
    product_img VARCHAR(255) NOT NULL
);

INSERT INTO Package_damaged (orderid, damaged_package_img)
VALUES 
    (5, 'https://i.imgur.com/R53x4rr.png '),
    (8, 'https://i.imgur.com/ElLuHVN.png'),
    (9, 'https://i.imgur.com/DNQTxC0.png');


CREATE TABLE Fraud_transaction (
	orderid INT PRIMARY KEY,
	product_img VARCHAR(255) NOT NULL
   -- we are not having the charged_price attribute here as we will cross check the recognized price with what in database on the fly
);


INSERT INTO Fraud_transaction (orderid, fraud_transaction_img)
VALUES 
	(10, 'https://i.imgur.com/CsDjUVs.png'),
    (12,'https://i.imgur.com/YUieKTf.png');


select * from customers;
select * from orders;
select * from products;
select * from Product_defect;
select * from Package_damaged;
select * from Fraud_transaction;
