# # ==========================================
# # CITIZEN CONNECT AI ANALYSIS SERVICE
# # ==========================================


# def analyze_grievance(subject, description):

#     # ==========================================
#     # PREPARE TEXT
#     # ==========================================

#     subject = subject or ""

#     description = description or ""


#     text = (
#         subject + " " + description
#     ).lower()


#     # ==========================================
#     # DEFAULT VALUES
#     # ==========================================

#     category = "General"

#     department = "Public Administration"

#     priority = "Medium"

#     reason = (
#         "The grievance has been classified for "
#         "review by the appropriate authority."
#     )


#     # ==========================================
#     # EMERGENCY / CRITICAL KEYWORDS
#     # ==========================================

#     emergency_words = [

#         "fire",

#         "accident",

#         "emergency",

#         "death",

#         "dead",

#         "injury",

#         "injured",

#         "danger",

#         "dangerous",

#         "gas leak",

#         "gas leakage",

#         "collapsed",

#         "collapse",

#         "flood",

#         "electrocution",

#         "electric shock",

#         "hospital emergency",

#         "life threatening",

#         "critical",

#         "blast",

#         "explosion"

#     ]


#     emergency_detected = any(

#         word in text

#         for word in emergency_words

#     )


#     # ==========================================
#     # ROAD & INFRASTRUCTURE
#     # ==========================================

#     if any(

#         word in text

#         for word in [

#             "road",

#             "pothole",

#             "potholes",

#             "street",

#             "highway",

#             "footpath",

#             "sidewalk",

#             "bridge",

#             "flyover",

#             "damaged road",

#             "broken road",

#             "construction road"

#         ]

#     ):

#         category = "Road & Infrastructure"

#         department = "Public Works Department"

#         reason = (
#             "The grievance contains keywords related "
#             "to roads or public infrastructure. It has "
#             "been assigned to the Public Works Department."
#         )


#     # ==========================================
#     # WATER & SANITATION
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "water",

#             "pipeline",

#             "water leakage",

#             "water leak",

#             "water supply",

#             "no water",

#             "drain",

#             "drainage",

#             "drain blocked",

#             "sewer",

#             "sewage",

#             "overflowing water",

#             "dirty water"

#         ]

#     ):

#         category = "Water & Sanitation"

#         department = "Water Supply Department"

#         reason = (
#             "The grievance appears related to water "
#             "supply, drainage, sanitation, or pipeline "
#             "infrastructure."
#         )


#     # ==========================================
#     # ELECTRICITY
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "electricity",

#             "electric",

#             "power",

#             "power cut",

#             "wire",

#             "electric wire",

#             "street light",

#             "streetlight",

#             "transformer",

#             "voltage",

#             "electric pole",

#             "power failure"

#         ]

#     ):

#         category = "Electricity"

#         department = "Electricity Department"

#         reason = (
#             "The grievance contains keywords related "
#             "to electricity, power supply, electrical "
#             "infrastructure, or street lighting."
#         )


#     # ==========================================
#     # CLEANLINESS & WASTE
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "garbage",

#             "waste",

#             "dirty",

#             "cleanliness",

#             "dustbin",

#             "trash",

#             "rubbish",

#             "litter",

#             "garbage collection",

#             "waste collection",

#             "unclean"

#         ]

#     ):

#         category = "Cleanliness & Waste"

#         department = "Municipal Corporation"

#         reason = (
#             "The grievance has been identified as a "
#             "cleanliness or waste management issue and "
#             "should be reviewed by the municipal authority."
#         )


#     # ==========================================
#     # PUBLIC SAFETY
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "crime",

#             "robbery",

#             "theft",

#             "unsafe",

#             "violence",

#             "police",

#             "assault",

#             "fight",

#             "harassment",

#             "threat",

#             "criminal"

#         ]

#     ):

#         category = "Public Safety"

#         department = "Police Department"

#         priority = "High"

#         reason = (
#             "The grievance contains public safety or "
#             "security-related keywords. Immediate review "
#             "by the appropriate safety authority is recommended."
#         )


#     # ==========================================
#     # HEALTH & MEDICAL
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "hospital",

#             "doctor",

#             "medical",

#             "health",

#             "ambulance",

#             "patient",

#             "medicine",

#             "clinic",

#             "disease",

#             "infection",

#             "healthcare"

#         ]

#     ):

#         category = "Health & Medical Services"

#         department = "Health Department"

#         reason = (
#             "The grievance appears related to public "
#             "health or medical services and has been "
#             "assigned to the Health Department."
#         )


#     # ==========================================
#     # TRAFFIC & TRANSPORT
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "traffic",

#             "traffic jam",

#             "congestion",

#             "bus",

#             "transport",

#             "parking",

#             "vehicle",

#             "signal",

#             "traffic signal"

#         ]

#     ):

#         category = "Traffic & Transport"

#         department = "Traffic Management Department"

#         reason = (
#             "The grievance contains transportation or "
#             "traffic-related keywords and should be "
#             "reviewed by the relevant transport authority."
#         )


#     # ==========================================
#     # GOVERNMENT / PUBLIC SERVICES
#     # ==========================================

#     elif any(

#         word in text

#         for word in [

#             "government office",

#             "municipal office",

#             "public service",

#             "official",

#             "government employee",

#             "certificate",

#             "document",

#             "application delayed",

#             "service delayed"

#         ]

#     ):

#         category = "Public Services"

#         department = "Public Administration"

#         reason = (
#             "The grievance appears related to a public "
#             "or government service and has been assigned "
#             "for administrative review."
#         )


#     # ==========================================
#     # EMERGENCY PRIORITY OVERRIDE
#     # ==========================================

#     if emergency_detected:

#         priority = "High"

#         reason = (
#             "Potential emergency or public safety keywords "
#             "were detected in the grievance. Immediate "
#             "attention is recommended."
#         )


#     # ==========================================
#     # HIGH PRIORITY CONDITIONS
#     # ==========================================

#     high_priority_conditions = [

#         "many people",

#         "serious problem",

#         "urgent",

#         "immediately",

#         "severe",

#         "major",

#         "completely blocked",

#         "risk to life",

#         "public danger"

#     ]


#     if any(

#         condition in text

#         for condition in high_priority_conditions

#     ):

#         priority = "High"


#     # ==========================================
#     # LOW PRIORITY CONDITIONS
#     # ==========================================

#     low_priority_conditions = [

#         "suggestion",

#         "feedback",

#         "minor",

#         "small issue",

#         "small problem",

#         "request",

#         "improvement suggestion"

#     ]


#     if priority != "High":

#         if any(

#             condition in text

#             for condition in low_priority_conditions

#         ):

#             priority = "Low"


#     # ==========================================
#     # CATEGORY-BASED PRIORITY IMPROVEMENT
#     # ==========================================

#     if priority == "Medium":


#         # Dangerous electrical problems

#         if category == "Electricity":

#             if any(

#                 word in text

#                 for word in [

#                     "exposed wire",

#                     "fallen wire",

#                     "electric shock",

#                     "sparking",

#                     "dangerous wire"

#                 ]

#             ):

#                 priority = "High"

#                 reason = (
#                     "A potentially dangerous electrical "
#                     "condition was detected. Immediate "
#                     "inspection is recommended."
#                 )


#         # Serious water problems

#         elif category == "Water & Sanitation":

#             if any(

#                 word in text

#                 for word in [

#                     "major leakage",

#                     "water flooding",

#                     "sewage overflow",

#                     "contaminated water"

#                 ]

#             ):

#                 priority = "High"

#                 reason = (
#                     "A serious water or sanitation issue "
#                     "was detected and may require urgent "
#                     "intervention."
#                 )


#         # Dangerous infrastructure

#         elif category == "Road & Infrastructure":

#             if any(

#                 word in text

#                 for word in [

#                     "large pothole",

#                     "road collapsed",

#                     "bridge damaged",

#                     "accident risk",

#                     "dangerous pothole"

#                 ]

#             ):

#                 priority = "High"

#                 reason = (
#                     "The infrastructure issue may create "
#                     "a public safety risk and requires "
#                     "urgent attention."
#                 )


#     # ==========================================
#     # FINAL ASSESSMENT
#     # ==========================================

#     return {

#         "category": category,

#         "department": department,

#         "priority": priority,

#         "reason": reason

#     }