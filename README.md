# Blockchain Chain of Custody #
***<ins>Program Description</ins>***
This program is meant to simulate a chain of custody breadcrumb system using blockchain mechanics. This was built as a group assignment for CSE 469 (DATA FORENSICS).

**Programmer(s):** Zion Esemonu, Nicholas Pinedo, Bryan Peterson, and Trevor Ransom

**Group:** 2

**Semester:** Spring 2023


***<ins>Actions available are as follows:</ins>***
- **bchoc add** *-c (case_id) -i (item_id)* - Add a new case to the blockchain file
- **bchoc init** - Sanity check. Only starts up and checks for the initial block.
- **bchoc checkout** *-i (item_id)* - Add a new checkout entry to the chain of custody for the given evidence item. Checkout actions may only be performed on evidence items that have already been added to the blockchain.
- **bchoc checkin** *-i (item_id)* - Add a new checkin entry to the chain of custody for the given evidence item. Checkin actions may only be performed on evidence items that have already been added to the blockchain.
- **bchoc log** *(-r option for displaying entries in reverse order) -n (num_entries) -c (case_id) -i (item_id)* -Display the blockchain entries giving the oldest first (unless -r is given).
- **bchoc remove** *-i (item_id) -y (reason) (-o owner)* - Prevents any further action from being taken on the evidence item specified. The specified item must have a state of CHECKEDIN for the action to succeed.
- **bchoc verify** - Parse the blockchain and validate all entries.
