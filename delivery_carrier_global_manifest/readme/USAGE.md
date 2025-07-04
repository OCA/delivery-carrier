To print the global manifest, you need to:

- Go to Inventory / Operations / Manifest
- Toggle the "Global Manifest Query" button
- Select the date
- Click the "Get Manifest File" button, then download the file


A delivery (picking) will be included in the global manifest only if all of the following conditions are met:

- Included carrier: The delivery has a carrier marked with "Include in Global Manifest".
- Done date: The date_done of the picking is within the selected date range in the wizard.
- State: The delivery is in "Done" state.
- Operation type: Only outgoing deliveries are considered (picking type = outgoing).
