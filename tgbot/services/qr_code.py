import qrcode


def qr_link(link):
    qr = qrcode.QRCode(
        version=7,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        # box_size=10,
        # border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    # img = qrcode.make(link)
    img.save("documents/qr_post_link.png")
    file = open("documents/qr_post_link.png", "rb")
    return file

