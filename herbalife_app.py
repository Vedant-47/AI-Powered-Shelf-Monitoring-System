import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
import os
from utils.detection import HerbalifeDetector

# Initialize detector and database
detector = HerbalifeDetector()
conn = sqlite3.connect('data/herbalife.db')

# App configuration
st.set_page_config(
    page_title="Herbalife Shelf Monitor",
    layout="wide",
    menu_items={
        'About': "Herbalife Product Recognition System v1.0"
    }
)

# Main menu (removed 'Product Management')
menu = st.sidebar.selectbox(
    "Menu", 
    ["Dashboard", "Shelf Analysis", "Alerts"]
)

if menu == "Dashboard":
    st.header("Herbalife Product Recognition")
    
    # Image upload and analysis
    uploaded_file = st.file_uploader(
        "Upload shelf photo (JPG/PNG)", 
        type=["jpg", "jpeg", "png"]
    )
    
    if uploaded_file:
        os.makedirs('data/herbalife_uploads', exist_ok=True)
        img_path = f"data/herbalife_uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        Image.open(uploaded_file).save(img_path)
        
        with st.spinner("Detecting Herbalife products..."):
            analysis = detector.analyze_shelf(img_path)
        
        if 'error' in analysis:
            st.error(f"Analysis error: {analysis['error']}")
        else:
            cols = st.columns(2)
            with cols[0]:
                st.image(img_path, caption="Uploaded Shelf Image")
            
            with cols[1]:
                if analysis['products']:
                    st.success(f"Detected {len(analysis['products'])} Herbalife products")
                    for product in analysis['products']:
                        with st.expander(f"{product['info'].get('type', 'Unknown')}"):
                            st.write(f"**Code:** {product['info'].get('code', 'N/A')}")
                            st.write(f"**Flavor:** {product['info'].get('flavor', 'N/A')}")
                            st.write(f"**Variant:** {product['info'].get('variant', 'N/A')}")
                else:
                    st.warning("No Herbalife products detected")

elif menu == "Shelf Analysis":
    st.header("Advanced Shelf Analysis")
    
    uploaded_file = st.file_uploader(
        "Upload high-quality shelf image", 
        type=["jpg", "jpeg", "png"]
    )
    
    if uploaded_file:
        img_path = f"data/herbalife_uploads/detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        Image.open(uploaded_file).save(img_path)
        
        analysis = detector.analyze_shelf(img_path)
        
        if 'error' in analysis:
            st.error(analysis['error'])
        else:
            st.image(img_path, use_column_width=True)
            
            if analysis['products']:
                st.subheader("Detection Results")
                for i, product in enumerate(analysis['products'], 1):
                    st.write(f"**Product {i}:**")
                    st.json(product['info'])
                    
                    img = Image.open(img_path)
                    cropped = img.crop((
                        product['bbox'][0], 
                        product['bbox'][1], 
                        product['bbox'][2], 
                        product['bbox'][3]
                    ))
                    st.image(cropped, caption=f"Product {i}")
            else:
                st.warning("No products detected")

elif menu == "Alerts":
    st.header("Product Alerts")
    
    alerts = conn.execute('''
    SELECT a.id, p.product_name, a.alert_type, a.alert_message, a.created_at
    FROM alerts a
    LEFT JOIN products p ON a.product_id = p.id
    WHERE a.resolved = FALSE
    ORDER BY a.created_at DESC
    ''').fetchall()
    
    if alerts:
        for alert in alerts:
            with st.container(border=True):
                cols = st.columns([4,1])
                cols[0].write(f"""
                **{alert[1] or 'Shelf Alert'}**  
                *{alert[2].replace('_', ' ').title()}*  
                {alert[3]}  
                *{alert[4]}*
                """)
                
                with cols[1]:
                    if st.button("Resolve", key=f"resolve_{alert[0]}"):
                        conn.execute(
                            'UPDATE alerts SET resolved = TRUE WHERE id = ?', 
                            (alert[0],)
                        )
                        conn.commit()
                        st.rerun()
    else:
        st.success("No active alerts")

conn.close()
