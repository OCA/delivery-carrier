# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


def assemble_zpl2_single_images(files):
    """Assemble a list of ZPL2 files with single image definition."""
    zpl_images = dict()
    zpl_labels = dict()
    # Extract all the images and labels from different files
    for file_nr, zpl_file in enumerate(files):
        # ^XA stands for label start
        images_def, label_def = zpl_file.split("^XA")
        label_def = "^XA%s" % label_def
        zpl_labels[file_nr] = label_def
        # ~DGR:IMGx stands for image start
        split_images = images_def.split("~DGR:IMG")
        # Remove header "^FXJob Header^FS" from image
        header = split_images.pop(0)
        # Add all the images for this file in zplimages
        if split_images:
            file_images = list()
            for img in split_images:
                zpl_image = "~DGR:IMG%s" % img
                file_images.append(zpl_image)
            zpl_images[file_nr] = file_images
    # Check images definition to avoid different images using the same ref
    # There are three cases to cover here:
    #  1. No existing image with this ref > keep image as it is
    #  2. Existing image with this ref is the same image > Nothing to do
    #  3. Existing image with this ref is not the same image > Change the ref
    #     for image and update refs in related label
    #  4. There is a same existing image with different ref > Update the refs
    #     in related label
    to_add_images = dict()
    for file_nr, file_zpl_images in zpl_images.items():
        for zpl_img in file_zpl_images:
            img_header, img_content = zpl_img.split(".GRF")
            img_number = img_header.lstrip("~DGR:")
            if img_content not in to_add_images.keys():
                if img_number not in to_add_images.values():
                    # Case 1. Keep image as it is
                    to_add_images[img_content] = img_number
                else:
                    # Case 3.
                    # Handle different image for same image numbers
                    max_img_number = max(to_add_images.values())
                    # Remove IMG form max_number_name in order to increment
                    img_prefix = max_img_number[:3]
                    digit = max_img_number[3:]
                    # Define new img number
                    new_digit = str(int(digit + 1))
                    new_img_number = img_prefix + new_digit
                    # change img number reference in label
                    to_add_images[img_content] = new_img_number
                    file_label = zpl_labels.get(file_nr)
                    file_label.replace(img_number, new_img_number)
                    zpl_labels[file_nr] = file_label
            elif img_number != to_add_images.get(img_content):
                # Case 4
                # Handle different image numbers for same image
                file_label = zpl_labels.get(file_nr)
                file_label.replace(img_number, to_add_images.get(img_content))
                zpl_labels[file_nr] = file_label
    # Construct final result
    res = header
    # Add all the images with their ref
    for img_to_add, img_number in to_add_images.items():
        res += "~DGR:%s.GRF%s" % (img_number, img_to_add)
    # Add all the updated labels
    for label in zpl_labels.values():
        res += header
        res += label
    return res


def assemble_zpl2(files):
    """Assemble a list of ZPL2 files."""
    return "".join(files)
