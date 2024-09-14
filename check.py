from multiprocessing.pool import ThreadPool as Pool

import pdfplumber


def extract_columns_from_page(page):
    left_bbox = (0, 0, 300, 783)
    right_bbox = (300, 0, 611.64, 783)
    # Extract text from the left column
    left_text = page.within_bbox(left_bbox).extract_text()
    # Extract text from the right column
    right_text = page.within_bbox(right_bbox).extract_text()

    return left_text, right_text


with pdfplumber.open("anatomy.pdf") as pdf:
    with Pool(8) as pool:
        lst = pool.map(extract_columns_from_page, pdf.pages)
        print("Done")
        print(lst)
    print("really done")
