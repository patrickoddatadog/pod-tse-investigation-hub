# JIRA Escalation Template

Use this template when writing up a JIRA escalation ticket.


## JIRA Ticket Format

**Title**

Create a suitable title that contains no more than 7 Words. Ideally less than 7.  

**Environment:**
- **Customer:** [Company name + ORG ID ZD ticket link]
- **Region:** [Datadog region]
- **Org ID** [Ord ID]
- **Account** [Account]


**Issue Description:**

[Clear description of what's happening]

**Expected Behavior:**
[What should happen]

**Impact:**
[How this affects the customer - data loss, missing monitors, can't deploy, etc.]

---

**Reproduction Steps:**

1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Result]


**Investigation Summary:**

[What you've investigated and ruled out]



**Screenshots/Evidence:**
Check cases/ZD-xxxxxx/assets
read the image name and attach.



**Additional Context:**
*This is Mandatory*
[Any other relevant information]
- Similar cases: [Link to related tickets]
- Documentation checked: [What docs you reviewed]
- Confluence searches: [What you searched for]


## Example: Good Escalation

**Title**
SAML - XML Metadata file failing to upload

**Environment:**
- **Customer:** NBCU - Consumer Data | (https://datadog.zendesk.com/agent/tickets/2819130)
- **Org ID** 564569
- **Account** Pro
- **Region:** US1

**Issue Description:**
Customer recieving the below error when attempting to upload Metadata.

”Failed to update SAML method Invalid metadata. Please review the issue and take appropriate action.”

They tried with the attached XML file. This XML file has shown XML validation errors when checked in a XML Validator trhrouhg an XML Validator, which produced the below errors

'Line: 1 | Column: 0  --> Element '{urn:oasis:names:tc:SAML:2.0:metadata}RoleDescriptor', attribute '{http://www.w3.org/2001/XMLSchema-instance}type': The QName value '{http://docs.oasis-open.org/wsfed/federation/200706}SecurityTokenServiceType' of the xsi:type attribute does not resolve to a type definition.
Line: 1 | Column: 0  --> Element '{urn:oasis:names:tc:SAML:2.0:metadata}RoleDescriptor': The type definition is abstract.
Line: 1 | Column: 0  --> Element '{urn:oasis:names:tc:SAML:2.0:metadata}RoleDescriptor', attribute '{http://www.w3.org/2001/XMLSchema-instance}type': The QName value '{http://docs.oasis-open.org/wsfed/federation/200706}ApplicationServiceType' of the xsi:type attribute does not resolve to a type definition.
Line: 1 | Column: 0  --> Element '{urn:oasis:names:tc:SAML:2.0:metadata}RoleDescriptor': The type definition is abstract.'

Addtionally, they have their Google Browser settings as Standard

**Expected Behavior:**
XML metadata file should be uploaded successfully.


**Impact:**
Customers end users are unable to login via SAML. As a result, users cannot login.

**Customer Priority:**
- **Severity:** High
- **Business Impact:** End users unable to login to the Platform. 


**Additional Context:**
- Similar case: WEBPS-7535, Engineering actively working on a fix.



