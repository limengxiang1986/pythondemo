
class UserModel():
    displayName = ''
    email = ''
    linemanagerEmail = ''
    linemanagerDisplayName = ''
    squadGroupName = ''
    tribeLeadEmail = ''
    tribeLeadDisplayName = ''
    tribename = ''
    uid = ''

    def __init__(self, displayName, email, linemanageremail, tribename, uid,linemanagerDisplayName='',
                 squadGroupName='',tribeLeadEmail='',tribeLeadDisplayName=''):
        self.displayName = displayName
        self.email = email
        self.linemanageremail = linemanageremail
        self.linemanagerDisplayName = linemanagerDisplayName
        self.tribename = tribename
        self.uid = uid
        self.squadGroupName = squadGroupName
        self.tribeLeadEmail = tribeLeadEmail
        self.tribeLeadDisplayName = tribeLeadDisplayName

    def __str__(self):
        return 'displayName:'+str(self.displayName ) +', email:'+str(self.email ) +', linemanagerEmail:'+str(self.linemanagerEmail ) +\
               ',linemanagerDisplayName:'+str(self.linemanagerDisplayName ) +', squadGroupName:'+str(self.squadGroupName ) +\
               ',tribeLeadEmail:'+str(self.tribeLeadEmail ) +', tribeLeadDisplayName:'+str(self.tribeLeadDisplayName ) +\
               ',tribename:'+str(self.tribename ) +', uid:'+str(self.uid )


class ApModel():
    APID = ''
    PRID = ''
    ApJiraId = ''
    APDescription = ''
    APCreatedDate = ''
    APDueDate = ''
    APCompletedOn = ''
    IsApCompleted = ''
    APAssingnedTo = ''
    QualityOwner = ''

    # New added for JIRA
    InjectionRootCauseEdaCause = ''
    RcaEdaCauseType = ''
    RcaEdaActionType = ''
    TargetRelease = ''
    CustomerAp = ''
    ApCategory = ''
    ShouldHaveBeenDetected = ''
    RcaEdaCauseCategory = ''
    EvidenceOfCompleteness = ''
    rca_pronto_ap_id = ''
    # End of added new field for JIRA

    def __init__(self, APID, PRID, APDescription, APCreatedDate, APDueDate, APCompletedOn, IsApCompleted, APAssingnedTo,
                 QualityOwner, ApJiraId,EvidenceOfCompleteness):
        self.APID = APID
        self.PRID = PRID
        self.ApJiraId = ApJiraId
        self.APDescription = APDescription
        self.APCreatedDate = APCreatedDate
        self.APDueDate = APDueDate
        self.APCompletedOn = APCompletedOn
        self.IsApCompleted = IsApCompleted
        self.APAssingnedTo = APAssingnedTo
        self.QualityOwner = QualityOwner
        self.EvidenceOfCompleteness = EvidenceOfCompleteness

        # # New added field for JIRA
        # self.InjectionRootCauseEdaCause = InjectionRootCauseEdaCause
        # self.RcaEdaCauseType = RcaEdaCauseType  # Escape Cause Category
        # self.RcaEdaActionType = RcaEdaActionType
        # self.TargetRelease = TargetRelease
        # self.CustomerAp = CustomerAp
        # self.ApCategory = ApCategory  # RCA/EDA
        # self.ShouldHaveBeenDetected = ShouldHaveBeenDetected
        # self.ApJiraId = ApJiraId
        # self.RcaEdaCauseCategory = RcaEdaCauseCategory  # Escape Cause Subcategory
        # self.rca_pronto_ap_id = rca_pronto_ap_id
        # # JIRA End
