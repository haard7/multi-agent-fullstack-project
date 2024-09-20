-- Query-1: Create a table named Products with the following columns:
-- make sure you are in the query tool of your database

CREATE TABLE Products (
	ProductID INT PRIMARY KEY,
	ProductName TEXT,
	ProductBrand TEXT,
	Gender TEXT,
	Price INT,
	NumImages INT,
	Description TEXT,
	PrimaryColor TEXT
);

-- Query-2
INSERT INTO
	Products (
		ProductID,
		ProductName,
		ProductBrand,
		Gender,
		Price,
		NumImages,
		Description,
		PrimaryColor
	)
VALUES
	(
		10017413,
		'Printed Medium Trolley Bag',
		'DKNY',
		'Unisex',
		11745,
		7,
		'Black and grey printed medium trolley bag, secured with a TSA lock. One handle on the top and one on the side, has a trolley with a retractable handle on the top and four corner mounted inline skate wheels. One main zip compartment, zip lining, two compression straps with click clasps, one zip compartment on the flap with three zip pockets. Warranty: 5 years. Warranty provided by Brand Owner / Manufacturer',
		'Black'
	),
	(
		10016283,
		'Women Beige & Grey Kurta Set',
		'EthnoVogue',
		'Women',
		5810,
		7,
		'Beige & Grey made to measure kurta with churidar and dupatta. Beige made to measure calf length kurta, has a V-neck, three-quarter sleeves, lightly padded on bust, flared hem, concealed zip closure. Grey solid made to measure churidar, drawstring closure. Grey net sequined dupatta, has printed taping. What is Made to Measure? Customised Kurta Set according to your Bust and Length. So please refer to the Size Chart to pick your perfect size. How to measure bust? Measure under your arms and around your chest to find your bust size in inches. How to measure Kurta length? Measure from shoulder till barefoot to find kurta length',
		'Beige'
	),
	(
		10009781,
		'SPYKAR Women Pink Cropped Jeans',
		'SPYKAR',
		'Women',
		899,
		7,
		'Pink coloured wash 5-pocket high-rise cropped jeans, clean look, no fade, has a button and zip closure, and waistband with belt loops',
		'Pink'
	),
	(
		10015921,
		'Raymond Men Blue Bandhgala Suit',
		'Raymond',
		'Men',
		5599,
		5,
		'Blue self-design bandhgala suit. Blue self-design bandhgala blazer, has a mandarin collar, single breasted with full button placket, long sleeves, three pockets, an attached lining and a double-vented back hem. Blue self-design mid-rise trousers, has a zip fly with a button and a hook-and-bar closure, four pockets, a waistband with belt loops',
		'Blue'
	),
	(
		10017833,
		'Parx Men Brown Casual Shirt',
		'Parx',
		'Men',
		759,
		5,
		'Brown and off-white printed casual shirt, has a spread collar, long sleeves, button placket, curved hem, one patch pocket',
		'White'
	),
	(
		10014361,
		'Men Brown Solid Slim Fit Regular Shorts',
		'SHOWOFF',
		'Men',
		791,
		5,
		'Brown solid low-rise regular shorts, has four pockets, a button closure',
		'Brown'
	);

(
	10017900,
	'Men Brown Solid Slim Fit Regular Shorts',
	'SHOWOFF',
	'Men',
	791,
	5,
	'Brown solid low-rise regular shorts, has four pockets, a button closure',
	'Black'
);

(
	10017901,
	'Pink Men Brown Solid Slim Fit Regular Shorts',
	'SHOWOFF',
	'Men',
	791,
	5,
	'Brown solid low-rise regular shorts, has four pockets, a button closure',
	'Pink'
);

-- Query for customer
CREATE TABLE Customers (
	CustomerID INT PRIMARY KEY,
	FirstName TEXT,
	LastName TEXT,
	Email TEXT,
	PhoneNumber TEXT,
	ShippingAddress TEXT
);

INSERT INTO
	Customers (
		CustomerID,
		FirstName,
		LastName,
		Email,
		PhoneNumber,
		ShippingAddress
	)
VALUES
	(
		1,
		'John',
		'Doe',
		'john.doe@example.com',
		'555-1234',
		'123 Elm Street'
	),
	(
		2,
		'Jane',
		'Smith',
		'jane.smith@example.com',
		'555-5678',
		'456 Oak Avenue'
	);

-- Queries for order status
CREATE TABLE Orders (
	OrderID INT PRIMARY KEY,
	CustomerID INT,
	ProductID INT,
	OrderDate DATE,
	Quantity INT,
	TotalPrice INT,
	OrderStatus TEXT,
	FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
	FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

INSERT INTO
	Orders (
		OrderID,
		CustomerID,
		ProductID,
		OrderDate,
		Quantity,
		TotalPrice,
		OrderStatus
	)
VALUES
	(
		1001,
		1,
		10017413,
		'2024-09-10',
		1,
		100,
		'Shipped'
	),
	(
		1002,
		2,
		10016283,
		'2024-09-11',
		2,
		300,
		'Delivered'
	),
	(
		1003,
		1,
		10016283,
		'2024-09-12',
		1,
		150,
		'Processing'
	);
